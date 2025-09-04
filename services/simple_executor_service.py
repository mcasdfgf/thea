# simple_executor_service.py: A basic cognitive service for direct LLM interactions.
# Its primary role is to handle tasks that require a straightforward, context-free
# response from the language model, such as generating the initial "instinctive"
# response at the beginning of a cognitive cycle.

from typing import Set, TYPE_CHECKING, Dict

from services.base import CognitiveService
from events import Task, Report, LinkDirective
from llm_interface import LLMInterface
from logger import logger
from prompts.service_prompts import EXECUTOR_PROMPT_TEMPLATE
from utils.reporting import create_report_meta

if TYPE_CHECKING:
    from orchestrator import Orchestrator
    from memory.memory_core import UniversalMemory


class SimpleExecutorService(CognitiveService):
    def __init__(self, orchestrator: "Orchestrator", memory: "UniversalMemory"):
        super().__init__("SimpleExecutorService", orchestrator, memory)
        self._llm = LLMInterface()
        self.system_prompt = EXECUTOR_PROMPT_TEMPLATE

    def get_supported_tasks(self) -> Set[str]:
        return {"generate_instinctive_response"}

    async def handle_task(self, task: Task) -> Report:
        """
        Handles `generate_instinctive_response` tasks.

        It constructs a simple prompt with the system message and the user's impulse
        (including conversation history if available) and forwards it to the LLM.
        """
        impulse_text = task.payload.get("impulse_text", "")

        history = task.payload.get("history", [])

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": impulse_text},
        ]
        if history:
            messages.extend(history)

        messages.append({"role": "user", "content": impulse_text})

        llm_response = await self._llm.generate(messages, temperature=0.6)
        response_text = llm_response.get("text", "Я не уверен, как на это ответить.")

        task_node = self._memory.get_node_by_attribute("task_id", task.task_id)
        link_to = (
            LinkDirective(target_id=task_node["id"], label="IS_RESULT_OF")
            if task_node
            else None
        )

        return Report(
            status="SUCCESS",
            data={"text": response_text},
            link_to=link_to,
            **create_report_meta(task)
        )
