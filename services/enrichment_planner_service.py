# enrichment_planner_service.py: A cognitive service responsible for deconstructing
# a user's request into a structured, actionable plan for memory retrieval.
# It uses an LLM with a specific tool (Pydantic model) to analyze the user's
# intent and generate a list of precise search queries for the MemoryRecallService.

from typing import Set, TYPE_CHECKING, Dict
from pydantic import BaseModel

from services.base import CognitiveService
from events import Task, Report
from llm_interface import LLMInterface
from logger import logger

from .planner_tools import MemorySearchQueries
from prompts.service_prompts import ENRICHMENT_PROMPT_TEMPLATE
from utils.reporting import create_report_meta

if TYPE_CHECKING:
    from orchestrator import Orchestrator
    from memory.memory_core import UniversalMemory


class EnrichmentPlannerService(CognitiveService):
    def __init__(self, orchestrator: "Orchestrator", memory: "UniversalMemory"):
        super().__init__("EnrichmentPlannerService", orchestrator, memory)
        self._llm = LLMInterface()
        self.system_prompt_template = ENRICHMENT_PROMPT_TEMPLATE
        self.tool_model = MemorySearchQueries

    def get_supported_tasks(self) -> Set[str]:
        return {"create_enrichment_plan"}

    def _pydantic_to_tool_schema(self, model: BaseModel) -> dict:
        """
        Converts a Pydantic model into a JSON schema compatible with the OpenAI Tools API.
        This allows the LLM to generate structured JSON output that can be directly
        validated by the Pydantic model.
        """
        schema = model.model_json_schema()
        parameters = {k: v for k, v in schema.items() if k != "title"}
        return {
            "type": "function",
            "function": {
                "name": schema["title"],
                "description": schema.get("description", ""),
                "parameters": parameters,
            },
        }

    async def handle_task(self, task: Task) -> Report:
        """
        Handles the `create_enrichment_plan` task.

        This method orchestrates the planning process:
        1.  Constructs a detailed prompt that includes the user's impulse and the system's initial instinct.
        2.  Provides the LLM with the `MemorySearchQueries` tool schema.
        3.  Forces the LLM to use this tool, ensuring a structured JSON output.
        4.  Validates the LLM's output against the Pydantic model.
        5.  Returns the validated plan as a dictionary in the report.
        """
        original_impulse = task.payload.get("original_impulse", "")
        instinctive_response = task.payload.get("instinctive_response", "")

        prompt = self.system_prompt_template.format(
            original_impulse=original_impulse, instinctive_response=instinctive_response
        )

        messages = [{"role": "system", "content": prompt}]
        tool_schema = self._pydantic_to_tool_schema(self.tool_model)
        tool_name = tool_schema["function"]["name"]

        try:
            response = await self._llm.client.chat.completions.create(
                model=self._llm.model_name,
                messages=messages,
                tools=[tool_schema],
                tool_choice={"type": "function", "function": {"name": tool_name}},
                temperature=0.0,
                max_tokens=4096,
            )
            tool_call = response.choices[0].message.tool_calls[0]
            arguments = tool_call.function.arguments
            try:
                validated_args = self.tool_model.model_validate_json(arguments)
                report_data = validated_args.model_dump()

                return Report(
                    status="SUCCESS", data=report_data, **create_report_meta(task)
                )
            except Exception as json_error:
                logger.warning(
                    self.service_name,
                    "Failed to parse JSON from LLM, returning empty plan.",
                    {"error": str(json_error), "raw_arguments": arguments},
                )

                # If the LLM output is malformed, return an empty plan.
                # This is a graceful failure, preventing the entire cycle from crashing.
                return Report(
                    status="SUCCESS", data={"queries": []}, **create_report_meta(task)
                )

        except Exception as e:
            logger.error(
                self.service_name,
                "LLM call failed during enrichment planning",
                {"error": str(e)},
                exc_info=True,
            )

            # In case of a catastrophic LLM failure, also return an empty plan
            # to allow the cognitive cycle to proceed without enrichment.
            return Report(
                status="SUCCESS", data={"queries": []}, **create_report_meta(task)
            )
