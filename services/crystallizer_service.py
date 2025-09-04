# crystallizer_service.py: A background service for the "slow" cognitive loop.
# It listens to a Redis queue for completed dialogue turns and performs the first
# level of reflection: crystallization. This process analyzes a user-assistant
# exchange, identifies key conceptual connections, and synthesizes them into new,
# atomic insights (`KnowledgeCrystalNode`).

import json
import re
from typing import Set, TYPE_CHECKING, List, Dict, Tuple
import redis.asyncio as redis
import asyncio

from services.base import CognitiveService
from events import Task, Report
from logger import logger
from llm_interface import LLMInterface
from config import (
    REDIS_HOST,
    REDIS_PORT,
    REDIS_DB_CRYSTALLIZER,
    CRYSTALLIZATION_QUEUE_KEY,
)
from prompts.service_prompts import (
    CRYSTALLIZER_PROMPT_TEMPLATE_1,
    CRYSTALLIZER_PROMPT_TEMPLATE_2,
)
from utils.reporting import create_report_meta

if TYPE_CHECKING:
    from orchestrator import Orchestrator
    from memory.memory_core import UniversalMemory


class CrystallizerService(CognitiveService):
    def __init__(self, orchestrator: "Orchestrator", memory: "UniversalMemory"):
        super().__init__("CrystallizerService", orchestrator, memory)
        self._llm = LLMInterface()
        self.redis_client = None
        if REDIS_HOST:
            try:
                self.redis_client = redis.Redis(
                    host=REDIS_HOST,
                    port=REDIS_PORT,
                    db=REDIS_DB_CRYSTALLIZER,
                    decode_responses=True,
                )
            except redis.exceptions.ConnectionError:
                logger.error(self.service_name, "Failed to connect to Redis.")

    async def _worker(self):
        """
        The main worker loop for the service.
        It continuously listens for new tasks from a Redis queue (`brpop`).
        This makes the crystallization process asynchronous and decoupled from the main
        request-response cycle.
        """
        if not self.redis_client:
            logger.warning(
                f"CognitiveService:{self.service_name}",
                "Redis is not configured. Worker will not start.",
            )
            return

        logger.info(
            f"CognitiveService:{self.service_name}",
            "Worker started in Redis polling mode.",
        )
        while self._is_running:
            try:
                raw_task = await self.redis_client.brpop(
                    CRYSTALLIZATION_QUEUE_KEY, timeout=1
                )
                if raw_task:
                    task_payload = json.loads(raw_task[1])
                    task = Task(type="crystallize_dialogue", payload=task_payload)
                    logger.info(
                        f"CognitiveService:{self.service_name}",
                        "New task received from Redis queue.",
                        task.payload,
                    )
                    asyncio.create_task(self._process_task_wrapper(task))
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    f"CognitiveService:{self.service_name}",
                    "Error in Redis worker loop.",
                    {"error": str(e)},
                    exc_info=True,
                )
                await asyncio.sleep(5)

    def get_supported_tasks(self) -> Set[str]:
        return {"crystallize_dialogue"}

    async def handle_task(self, task: Task) -> Report:
        """
        Handles the `crystallize_dialogue` task.

        This is the core logic for Level 1 Reflection:
        1.  Retrieves the dialogue turn (impulse + response) from memory.
        2.  Extracts the associated concepts.
        3.  Uses an LLM to identify the most significant pairs of concepts.
        4.  For each pair, uses the LLM to synthesize a concise insight explaining their connection.
        5.  Records each new insight as a `KnowledgeCrystalNode` in UniversalMemory.
        """
        impulse_id = task.payload.get("impulse_id")
        if not impulse_id or not self._memory.graph.has_node(impulse_id):
            return Report(
                status="FAILURE",
                data={"error": "impulse_id not found or node does not exist"},
                **create_report_meta(task),
            )

        final_response_node_data = None
        for pred_id in self._memory.graph.predecessors(impulse_id):
            node_data = self._memory.graph.nodes[pred_id]
            if node_data.get("type") == "FinalResponseNode":
                edge_data = self._memory.graph.get_edge_data(pred_id, impulse_id)
                if edge_data and edge_data.get("label") == "IS_RESPONSE_TO":
                    final_response_node_data = node_data
                    break

        if not final_response_node_data:
            return Report(
                status="SUCCESS",
                data={
                    "message": "No corresponding FinalResponseNode found for the impulse."
                },
                **create_report_meta(task),
            )

        concepts = [
            self._memory.graph.nodes[succ_id].get("content")
            for succ_id in self._memory.graph.successors(impulse_id)
            if self._memory.graph.nodes[succ_id].get("type") == "ConceptNode"
        ]

        if len(concepts) < 2:
            return Report(
                status="SUCCESS",
                data={
                    "message": "Not enough concepts to form a connection (minimum 2 required)."
                },
                **create_report_meta(task),
            )

        impulse_text = self._memory.graph.nodes[impulse_id].get("content", "")
        response_text = final_response_node_data.get("content", "")
        dialog_text = f"Пользователь: {impulse_text}\nАссистент: {response_text}"

        key_pairs = await self._extract_key_pairs(concepts)

        generated_crystals = []
        for pair in key_pairs:
            insight_content = await self._summarize_connection(pair, dialog_text)

            crystal_id = self._memory.record_entry(
                node_type="KnowledgeCrystalNode",
                content=insight_content,
                attributes={
                    "source_concepts": ", ".join(sorted(pair)),
                    "source_impulse": impulse_id,
                    "active_status": 1,
                    "strength": 1,
                },
            )

            if crystal_id:
                for concept_name in pair:
                    concept_id = self._memory.get_or_create_concept_node(concept_name)
                    if concept_id:
                        self._memory.graph.add_edge(
                            crystal_id, concept_id, label="INSIGHT_FROM_CONCEPT"
                        )
                generated_crystals.append({"pair": pair, "crystal_id": crystal_id})

        if not generated_crystals:
            return Report(
                status="SUCCESS",
                data={
                    "message": "Failed to generate any new insights from the dialogue."
                },
                **create_report_meta(task),
            )

        report_data = {"generated_crystals": generated_crystals}
        return Report(status="SUCCESS", data=report_data, **create_report_meta(task))

    async def _extract_key_pairs(self, concepts: List[str]) -> List[Tuple[str, str]]:
        """Uses the LLM to identify the most important conceptual pairs from a list."""
        if len(concepts) < 2:
            return []

        concept_list_str = ", ".join(f'"{c}"' for c in sorted(list(set(concepts))))

        system_prompt = CRYSTALLIZER_PROMPT_TEMPLATE_1
        user_content = (
            f"From this list of Russian concepts, extract the 2 most important pairs.\n"
            f"Concepts: [{concept_list_str}].\n"
            f'Your output must be only a valid JSON list of lists. Example: `[["кофе", "пресс"], ["френч", "пресс"]]`'
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        response = await self._llm.generate(messages, temperature=0.5)
        text_response = response.get("text", "[]")

        try:
            match = re.search(r"\[\s*\[.*?\]\s*\]", text_response, re.DOTALL)
            if not match:
                return []

            parsed_list = json.loads(match.group(0))
            if isinstance(parsed_list, list):
                unique_pairs = {
                    tuple(sorted(p))
                    for p in parsed_list
                    if isinstance(p, list) and len(p) == 2
                }
                return list(unique_pairs)
        except (json.JSONDecodeError, TypeError):
            logger.error(
                "CrystallizerService",
                "Failed to parse key pairs JSON from LLM response.",
                {"response": text_response},
            )
        return []

    async def _summarize_connection(
        self, pair: Tuple[str, str], dialog_text: str
    ) -> str:
        """Uses the LLM to generate a single-sentence insight explaining the connection between two concepts."""
        system_prompt = CRYSTALLIZER_PROMPT_TEMPLATE_2
        user_content = (
            f"Dialogue:\n---\n{dialog_text}\n---\n\n"
            f"Based on the dialogue, concisely explain the connection between these two Russian concepts: `{pair[0]}` and `{pair[1]}`. "
            f"Your answer must be a single, meaningful sentence in Russian."
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]
        response = await self._llm.generate(messages, temperature=0.5)
        return response.get("text", f"Could not summarize the connection for {pair}.")
