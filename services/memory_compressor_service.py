# memory_compressor_service.py: A specialized service for data distillation.
# This service's primary role is to take a conversational turn (a user query
# and an assistant's response) and compress it into a concise, meaningful summary.
# This is a core component of the archival process, which prepares data for
# the creation of "Golden Datasets" for future model finetuning.

import json
from typing import Set, TYPE_CHECKING, Dict, List

from services.base import CognitiveService
from events import Task, Report
from llm_interface import LLMInterface
from logger import logger
from prompts.service_prompts import DISTILLER_PROMPT_TEMPLATE
from utils.reporting import create_report_meta

if TYPE_CHECKING:
    from orchestrator import Orchestrator
    from memory.memory_core import UniversalMemory


class MemoryCompressorService(CognitiveService):
    def __init__(self, orchestrator: "Orchestrator", memory: "UniversalMemory"):
        super().__init__("MemoryCompressorService", orchestrator, memory)
        self._llm = LLMInterface()

    def get_supported_tasks(self) -> Set[str]:
        # This service now responds to direct, on-demand tasks from the Orchestrator.
        return {"compress_memory_chunk"}

    async def handle_task(self, task: Task) -> Report:
        """
        Handles `compress_memory_chunk` tasks, specifically for dialogue distillation.

        It expects a list containing exactly two items: the user turn and the assistant turn.
        It then uses an LLM to generate a one or two-sentence summary of the exchange.
        """
        items_to_process = task.payload.get("items_to_compress", [])

        if not items_to_process:
            return Report(
                status="SUCCESS", data={"summary_text": ""}, **create_report_meta(task)
            )

        if len(items_to_process) != 2:
            return Report(
                status="FAILURE",
                data={"error": "Distillation requires exactly one pair of turns."},
                **create_report_meta(task),
            )

        user_text = items_to_process[0].get("content", "")
        assistant_text = items_to_process[1].get("content", "")

        system_prompt = DISTILLER_PROMPT_TEMPLATE
        prompt = f'User: "{user_text}"\nAssistant: "{assistant_text}"\n\nDistill this exchange into one or two meaningful sentences.'

        response = await self._llm.generate(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ]
        )
        distillate_text = response.get("text", "Distillation failed.")
        return Report(
            status="SUCCESS",
            data={"summary_text": distillate_text},
            **create_report_meta(task),
        )
