# orchestrator.py: The central coordinator of the T.H.E.A. cognitive architecture.
# It manages the flow of information between cognitive services, handles the main
# cognitive cycle, and maintains the short-term conversation context.

import asyncio
import json
from typing import Dict, Any, List, Optional, TYPE_CHECKING
import collections
from dataclasses import asdict
import requests
import functools
import redis.asyncio as redis

from events import Task, Report, LinkDirective
from memory.memory_core import UniversalMemory
from logger import logger
from config import (
    REDIS_HOST,
    REDIS_PORT,
    REDIS_DB_CRYSTALLIZER,
    LLM_CONTEXT_LIMIT,
    CONTEXT_SUMMARY_TRIGGER_PERCENTAGE,
    CONVERSATION_CACHE_MAXLEN,
    VLLM_TOKENIZER_URL,
    CRYSTALLIZATION_QUEUE_KEY,
)


END_OF_MESSAGE = "\n\n__END_OF_MESSAGE__\n\n"

if TYPE_CHECKING:
    from services.synthesis_service import SynthesisService
    from services.base import CognitiveService


class Orchestrator:
    def __init__(self, memory: UniversalMemory):
        self._memory = memory
        self._services: Dict[str, CognitiveService] = {}
        self._task_routing_table: Dict[str, CognitiveService] = {}
        self._report_futures: Dict[str, asyncio.Future] = {}
        self._conversation_cache = collections.deque()
        self.TOKENIZER_URL = VLLM_TOKENIZER_URL
        self.SUMMARY_THRESHOLD = int(
            LLM_CONTEXT_LIMIT * CONTEXT_SUMMARY_TRIGGER_PERCENTAGE
        )

        # Initialize Redis client for asynchronous background task queuing.
        try:
            self.redis_client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB_CRYSTALLIZER,
                decode_responses=True,
            )
            logger.info("Orchestrator", "Successfully connected to Redis.")
        except redis.exceptions.ConnectionError as e:
            logger.error(
                "Orchestrator", "Failed to connect to Redis.", {"error": str(e)}
            )
            self.redis_client = None

    # --- Context and Memory Management ---
    def _sanitize_report_for_payload(self, report: Report) -> Dict:
        """
        Creates a clean, flat dictionary from a Report object,
        suitable for being stored as a payload in another node's content.
        Prevents recursive bloating.
        """
        if not report or not report.data:
            return {}

        clean_data = report.data.copy()

        if "found_nodes" in clean_data:
            clean_data["found_nodes_summary"] = [
                {
                    "id": node.get("id", "N/A")[:8],
                    "type": node.get("type", "N/A"),
                    "score": round(node.get("relevance_score", 0), 2),
                }
                for node in clean_data["found_nodes"]
            ]
            del clean_data["found_nodes"]

        clean_report = {"source_task_type": report.source_task_type, "data": clean_data}
        return clean_report

    async def _distill_and_archive_pair(self, user_turn: dict, assistant_turn: dict):
        """
        A background task to distill and archive a single user-assistant turn.
        This process creates a `DialogueTurnNode` to store a compressed summary
        of the interaction, linking it to the original nodes for traceability.
        This is a key part of the "Golden Dataset" creation for future finetuning.
        """
        try:
            user_impulse_node_id = user_turn.get("node_id")
            assistant_response_node_id = assistant_turn.get("node_id")

            if not user_impulse_node_id or not assistant_response_node_id:
                logger.warning(
                    "Distillation",
                    "Skipping cache item without a node_id.",
                    {"item": user_turn},
                )
                return

            logger.info(
                "Distillation",
                "Starting dialogue turn archival.",
                {"impulse_id": user_impulse_node_id},
            )

            dialogue_turn_node_id = self._memory.record_entry(
                node_type="DialogueTurnNode",
                content="Awaiting distillation...",
                attributes={
                    "archived_node_ids": {
                        "impulse_id": user_impulse_node_id,
                        "response_id": assistant_response_node_id,
                    }
                },
            )

            if dialogue_turn_node_id:
                self._memory.graph.add_edge(
                    dialogue_turn_node_id,
                    user_impulse_node_id,
                    label="ARCHIVES_IMPULSE",
                )
                self._memory.graph.add_edge(
                    dialogue_turn_node_id,
                    assistant_response_node_id,
                    label="ARCHIVES_RESPONSE",
                )

                distill_task = Task(
                    type="compress_memory_chunk",
                    payload={
                        "items_to_compress": [user_turn, assistant_turn],
                        "is_distillation": True,
                    },
                )
                report = await self.execute_single_task(distill_task)
                distillate_text = report.data.get(
                    "summary_text", "Distillation failed."
                )

                self._memory.graph.nodes[dialogue_turn_node_id][
                    "content"
                ] = distillate_text

                for successor_id in self._memory.graph.successors(user_impulse_node_id):
                    node_data = self._memory.graph.nodes.get(successor_id, {})
                    if node_data.get("type") == "ConceptNode":
                        self._memory.graph.add_edge(
                            dialogue_turn_node_id,
                            successor_id,
                            label="CONTAINS_CONCEPT",
                        )

                logger.info(
                    "Distillation",
                    "Dialogue turn archived successfully.",
                    {"turn_node_id": dialogue_turn_node_id},
                )

        except Exception as e:
            logger.error(
                "Distillation",
                "Error in background distillation task.",
                {"error": str(e)},
                exc_info=True,
            )

    async def _manage_context(self, impulse_text: str):
        """
        Implements a "Smart FIFO" cache management strategy.
        It monitors the token size of the conversation cache and, when it exceeds
        a threshold, offloads the oldest turn pair to the background distillation
        and archival process (`_distill_and_archive_pair`).
        """

        impulse_tokens_estimate = len(impulse_text) / 3

        full_text_to_tokenize = "\n".join(
            [msg.get("content", "") for msg in self._conversation_cache]
        )
        if not full_text_to_tokenize.strip():
            return

        try:
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None,
                functools.partial(
                    requests.post,
                    self.TOKENIZER_URL,
                    json={"prompt": full_text_to_tokenize},
                ),
            )
            response.raise_for_status()
            cache_token_count = len(response.json().get("tokens", []))
        except requests.RequestException as e:
            logger.error(
                "ContextManager",
                "Error calling vLLM tokenizer, aborting cleanup.",
                {"error": str(e)},
            )
            return

        total_size = cache_token_count + impulse_tokens_estimate

        safe_limit = int(LLM_CONTEXT_LIMIT * 0.7)

        logger.info(
            "ContextManager",
            "Checking cache token limits.",
            {
                "cache_tokens": cache_token_count,
                "impulse_estimate": int(impulse_tokens_estimate),
                "total_future_size": int(total_size),
                "safe_limit": safe_limit,
                "is_exceeded": total_size > safe_limit,
            },
        )

        if total_size <= safe_limit:
            return

        logger.warning(
            "ContextManager",
            f"Cache size ({total_size:.0f}) exceeds safe limit ({safe_limit:.0f}). Starting FIFO cleanup.",
        )

        while total_size > safe_limit and len(self._conversation_cache) >= 2:
            user_turn = self._conversation_cache.popleft()
            assistant_turn = self._conversation_cache.popleft()

            asyncio.create_task(
                self._distill_and_archive_pair(user_turn, assistant_turn)
            )

            total_size -= (
                len(user_turn.get("content", ""))
                + len(assistant_turn.get("content", ""))
            ) / 3

        logger.info(
            "ContextManager",
            f"Cleanup complete. New estimated cache size: ~{total_size:.0f} tokens.",
        )

    # --- Task and Service Management ---
    async def execute_single_task(self, task: Task) -> Report:
        task_node_id = self._memory.record_entry(
            node_type="TaskNode",
            content=task.payload,
            attributes={
                "task_type": task.type,
                "task_id": task.task_id,
                "correlation_id": task.correlation_id,
            },
            links=[task.link_to] if task.link_to else [],
        )

        future = await self.submit_task(task)
        if future:
            report = await future
            if report.report_node_id and task_node_id:
                self._memory.graph.add_edge(
                    report.report_node_id, task_node_id, label="IS_RESULT_OF"
                )
            return report

        return Report(
            status="FAILURE",
            data={"error": "Failed to create task future."},
            correlation_id=task.correlation_id,
            source_task_id=task.task_id,
            source_task_type=task.type,
        )

    def register_service(self, service: "CognitiveService"):
        """Registers a cognitive service, making it available for task routing."""
        service_name = service.service_name
        self._services[service_name] = service
        for task_type in service.get_supported_tasks():
            self._task_routing_table[task_type] = service
        logger.info(
            "Orchestrator",
            f"Service '{service_name}' registered. Supports: {list(service.get_supported_tasks())}",
        )

    async def start_all_services(self):
        for s in self._services.values():
            await s.start()

    async def stop_all_services(self):
        for s in self._services.values():
            await s.stop()

    async def submit_task(self, task: Task) -> Optional[asyncio.Future]:
        service = self._task_routing_table.get(task.type)
        if not service:
            logger.error(
                "Orchestrator", f"No service found for task type '{task.type}'"
            )
            return None

        future = asyncio.get_running_loop().create_future()
        self._report_futures[task.task_id] = future
        await service.push_task(task)
        return future

    async def receive_report(self, report: Report):
        report_node_id = self._memory.record_entry(
            node_type="ReportNode",
            content=report.data,
            attributes={"service": report.source_task_type, "status": report.status},
        )
        if report:
            report.report_node_id = report_node_id
        future = self._report_futures.pop(report.source_task_id, None)
        if future:
            future.set_result(report)

    # --- Core Cognitive Cycle ---
    async def handle_user_impulse(
        self, impulse_text: str, writer: asyncio.StreamWriter
    ) -> Optional[str]:
        """
        Handles the main cognitive cycle for a user impulse (v5).
        This process involves six distinct stages:
        1.  **Initiation**: Manages context and records the user's raw input.
        2.  **Instinct**: Generates a fast, context-free initial response.
        3.  **Enrichment Planning**: Deconstructs the request to determine what information is needed from memory.
        4.  **Enrichment Execution**: Queries the memory based on the generated plan.
        5.  **Final Synthesis**: Combines the instinctual response with retrieved memories to form the final, context-aware answer.
        6.  **Closure**: Records the final response, updates the conversation cache, and queues the interaction for background crystallization.
        """
        await self._manage_context(impulse_text)

        logger.info(
            "Orchestrator:FinalCycle",
            "--- CYCLE START ---",
            {"impulse": impulse_text},
        )

        impulse_node_id = self._memory.record_entry(
            node_type="UserImpulse", content=impulse_text
        )
        if not impulse_node_id:
            return None
        history_for_llm = list(self._conversation_cache)

        instinct_report = await self.execute_single_task(
            Task(
                type="generate_instinctive_response",
                payload={"impulse_text": impulse_text, "history": history_for_llm},
                link_to=LinkDirective(target_id=impulse_node_id, label="IS_TASK_FOR"),
            )
        )
        instinctive_response_text = instinct_report.data.get("text", "")
        instinctive_response_node_id = self._memory.record_entry(
            node_type="InstinctiveResponseNode",
            content=instinctive_response_text,
            links=[LinkDirective(target_id=impulse_node_id, label="IS_INSTINCT_FOR")],
        )

        enrichment_plan_report = await self.execute_single_task(
            Task(
                type="create_enrichment_plan",
                payload={
                    "original_impulse": impulse_text,
                    "instinctive_response": instinctive_response_text,
                },
                link_to=LinkDirective(target_id=impulse_node_id, label="IS_TASK_FOR"),
            )
        )

        enrichment_reports = []
        if (
            enrichment_plan_report.status == "SUCCESS"
            and enrichment_plan_report.report_node_id
        ):
            search_plan_node_id = self._memory.record_entry(
                node_type="SearchPlanNode",
                content=enrichment_plan_report.data,
                links=[
                    LinkDirective(
                        target_id=enrichment_plan_report.report_node_id,
                        label="CONTAINS_PLAN",
                    )
                ],
            )

            search_queries = enrichment_plan_report.data.get("queries", [])
            all_concepts = {
                concept.lower().strip()
                for query in search_queries
                for concept in query.get("concepts", [])
                if concept
            }
            if all_concepts:
                for concept_name in all_concepts:
                    concept_id = self._memory.get_or_create_concept_node(concept_name)
                    if concept_id:
                        self._memory.graph.add_edge(
                            impulse_node_id, concept_id, label="CONTAINS_CONCEPT"
                        )

            search_futures = []
            for query_data in search_queries:
                search_task = Task(
                    type="recall_request",
                    payload={"request_payload": query_data},
                    link_to=LinkDirective(
                        target_id=search_plan_node_id, label="IS_TASK_FOR"
                    ),
                )
                search_futures.append(self.execute_single_task(search_task))

            if search_futures:
                enrichment_reports = await asyncio.gather(*search_futures)

        final_report = await self.execute_single_task(
            Task(
                type="synthesize_final_response",
                payload={
                    "original_impulse": impulse_text,
                    "instinctive_response": instinctive_response_text,
                    "memory_package": [asdict(r) for r in enrichment_reports if r],
                },
                link_to=LinkDirective(target_id=impulse_node_id, label="IS_TASK_FOR"),
            )
        )
        final_response_text = final_report.data.get(
            "text", "An error occurred during synthesis."
        )

        final_response_node_id = self._memory.record_entry(
            node_type="FinalResponseNode",
            content=final_response_text,
            links=[
                LinkDirective(target_id=impulse_node_id, label="IS_RESPONSE_TO"),
                LinkDirective(
                    target_id=final_report.report_node_id, label="WAS_SYNTHESIZED_FROM"
                ),
            ],
        )

        self._conversation_cache.append(
            {"role": "user", "content": impulse_text, "node_id": impulse_node_id}
        )
        self._conversation_cache.append(
            {
                "role": "assistant",
                "content": final_response_text,
                "node_id": final_response_node_id,
            }
        )

        if self.redis_client:
            try:
                await self.redis_client.lpush(
                    CRYSTALLIZATION_QUEUE_KEY,
                    json.dumps({"impulse_id": impulse_node_id}),
                )
            except Exception as e:
                logger.error(
                    "Orchestrator",
                    "Failed to push crystallization task to Redis.",
                    {"error": str(e)},
                )

        await self.send_response_message(writer, final_response_text)
        # --- Automatic save after the cognitive cycle ---
        self._memory.close()
        logger.info("Orchestrator", "Automatic save triggered after cognitive cycle.")

        logger.info("Orchestrator:FinalCycle", "--- CYCLE END ---")
        return impulse_node_id

    # --- Client Communication ---
    async def send_response_message(self, writer: asyncio.StreamWriter, message: str):
        await self._send_to_writer(writer, "RESPONSE", message)

    async def send_system_message(self, writer: asyncio.StreamWriter, message: str):
        await self._send_to_writer(writer, "SYSTEM", message)

    async def _send_to_writer(
        self, writer: asyncio.StreamWriter, msg_type: str, message: str
    ):
        if writer and not writer.is_closing():
            full_message = f"{msg_type}:::{message}{END_OF_MESSAGE}"
            writer.write(full_message.encode("utf-8"))
            await writer.drain()
