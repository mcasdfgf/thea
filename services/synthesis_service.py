# synthesis_service.py: The final stage of the cognitive cycle.
# This service is responsible for generating the definitive, context-aware response
# to the user. It takes the initial "instinctive" response and the package of
# retrieved memories, then synthesizes them into a single, coherent answer.
# It also includes logic to manage the LLM's context window by dynamically
# selecting which memories to include based on a token budget.

import json
import asyncio
import requests
import functools
from config import LLM_CONTEXT_LIMIT, VLLM_TOKENIZER_URL

# --- Prompt Engineering Note ---
# This service was refactored to use a two-part prompt structure (system instructions + user data template)
# instead of a single large prompt. This provides more reliable behavior with modern instruction-tuned LLMs.
# Some legacy code related to the old single-prompt format is intentionally left commented out below
# to facilitate future experiments with different prompting strategies.
from prompts.service_prompts import SYNTHESIS_SYSTEM_PROMPT, SYNTHESIS_USER_TEMPLATE # SYNTHESIS_PROMPT_TEMPLATE
# -----------------------------

from typing import Set, TYPE_CHECKING, Dict

from services.base import CognitiveService
from events import Task, Report, LinkDirective
from llm_interface import LLMInterface
from logger import logger
from utils.reporting import create_report_meta
from utils.token_utils import count_tokens

if TYPE_CHECKING:
    from orchestrator import Orchestrator
    from memory.memory_core import UniversalMemory


class SynthesisService(CognitiveService):
    def __init__(self, orchestrator: "Orchestrator", memory: "UniversalMemory"):
        super().__init__("SynthesisService", orchestrator, memory)
        self._llm = LLMInterface()
        self.tokenizer_url = VLLM_TOKENIZER_URL
        self.system_prompt_template = SYNTHESIS_SYSTEM_PROMPT # SYNTHESIS_PROMPT_TEMPLATE
        self.user_prompt_template = SYNTHESIS_USER_TEMPLATE

    async def _count_tokens(self, text: str) -> int:
        """Sends text to the vLLM tokenizer endpoint and returns the token count."""
        if not text.strip() or not self.tokenizer_url:
            return 0
        try:
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None,
                functools.partial(
                    requests.post, self.tokenizer_url, json={"prompt": text}
                ),
            )
            response.raise_for_status()
            return len(response.json().get("tokens", []))
        except requests.RequestException as e:
            logger.warning(
                self.service_name, f"Could not count tokens: {e}. Returning 0."
            )
            return 0

    def get_supported_tasks(self) -> Set[str]:
        return {"synthesize_final_response", "synthesize_acknowledgement"}

    async def handle_task(self, task: Task) -> Report:
        """Routes the task to the appropriate handler based on its type."""
        if task.type == "synthesize_final_response":
            return await self._handle_synthesis(task)
        elif task.type == "synthesize_acknowledgement":
            return await self._handle_acknowledgement(task)

        return Report(
            status="FAILURE",
            data={"error": "Unsupported synthesis task type"},
            **create_report_meta(task),
        )

    async def _handle_synthesis(self, task: Task) -> Report:
        """
        Handles the `synthesize_final_response` task.

        This method implements a "greedy knapsack" algorithm for context packing:
        1.  It gathers all unique memory nodes found during the recall stage.
        2.  It calculates the token size of the static parts of the prompt (user impulse, instructions).
        3.  It determines a "token budget" available for including retrieved memories.
        4.  It iterates through the memory nodes (sorted by relevance) and adds them
            to the prompt until the budget is exhausted.
        5.  Finally, it sends the complete, packed prompt to the LLM for generation.
        """
        payload = task.payload
        original_impulse = payload.get("original_impulse", "")
        instinctive_response = payload.get("instinctive_response", "")
        memory_package_list = payload.get("memory_package", [])

        all_found_nodes = []
        for report_dict in memory_package_list:
            found_nodes_in_report = report_dict.get("data", {}).get("found_nodes", [])
            all_found_nodes.extend(found_nodes_in_report)

        unique_nodes = list({node["id"]: node for node in all_found_nodes}.values())
        unique_nodes.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

        # base_prompt_text = self.system_prompt_template.format(
        #     original_impulse=original_impulse,
        #     instinctive_response=instinctive_response,
        #     memory_package="",
        # )

        system_prompt_tokens = await count_tokens(self.system_prompt_template)
        user_template_filled = self.user_prompt_template.format(
            original_impulse=original_impulse,
            instinctive_response=instinctive_response,
            memory_package="", # Empty package for calculation
        )
        user_template_tokens = await count_tokens(user_template_filled)
        
        # base_tokens = await count_tokens(base_prompt_text)
        base_tokens = system_prompt_tokens + user_template_tokens
        
        RESERVE_FOR_RESPONSE = 3072

        SAFETY_MARGIN = 100

        memory_budget_tokens = (
            LLM_CONTEXT_LIMIT - base_tokens - RESERVE_FOR_RESPONSE - SAFETY_MARGIN
        )

        logger.info(
            self.service_name,
            "Calculating token budget for memory context",
            {
                "total_limit": LLM_CONTEXT_LIMIT,
                "base_prompt_tokens": base_tokens,
                "reserved_for_response": RESERVE_FOR_RESPONSE,
                "memory_budget": memory_budget_tokens,
            },
        )

        memory_findings_str = ""
        current_memory_tokens = 0

        if not unique_nodes:
            memory_findings_str = "- В моей памяти не нашлось релевантной информации."
        else:
            findings_lines = []
            for node in unique_nodes:
                node_type = node.get("type", "Unknown")
                content = str(node.get("content", ""))
                line = f"- (Источник: {node_type}): {content}\n"

                line_tokens = await self._count_tokens(line)

                if current_memory_tokens + line_tokens <= memory_budget_tokens:
                    findings_lines.append(line)
                    current_memory_tokens += line_tokens
                else:
                    logger.warning(
                        self.service_name,
                        "Memory budget exceeded, skipping node",
                        {"node_id": node.get("id")},
                    )
                    break

            if not findings_lines:
                memory_findings_str = "- В моей памяти не нашлось релевантной информации (все найденное не влезло в контекст)."
            else:
                memory_findings_str = "".join(findings_lines)

        # final_prompt = self.system_prompt_template.format(
        #     original_impulse=original_impulse,
        #     instinctive_response=instinctive_response,
        #     memory_package=memory_findings_str,
        # )

        user_prompt_with_data = self.user_prompt_template.format(
            original_impulse=original_impulse,
            instinctive_response=instinctive_response,
            memory_package=memory_findings_str,
        )


        # messages = [{"role": "user", "content": final_prompt}]
        messages = [
            {"role": "system", "content": SYNTHESIS_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt_with_data}
        ]
        
        llm_response = await self._llm.generate(
            messages,
            temperature=0.7,
            max_tokens=3072,
        )
        final_text = llm_response.get(
            "text", "К сожалению, я не смог сформировать окончательный ответ."
        )

        return Report(
            status="SUCCESS", data={"text": final_text}, **create_report_meta(task)
        )

    async def _handle_acknowledgement(self, task: Task) -> Report:
        """Generates a simple, natural language acknowledgement (e.g., for `!fact` commands)."""
        hint = task.payload.get("hint", "Got it, I've stored that information.")
        system_prompt = "You are a helpful assistant. Your task is to provide a brief, natural, and confirmatory response in Russian based on an internal hint."
        prompt = f"Internal hint: '{hint}'. Formulate your user-facing response."

        response = await self._llm.generate(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ]
        )
        text = response.get("text", "Хорошо, я запомнил.")
        return Report(status="SUCCESS", data={"text": text}, **create_report_meta(task))
