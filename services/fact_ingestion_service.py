# fact_ingestion_service.py: A service for directly injecting knowledge into memory.
# It handles the `!fact` command, allowing a user to insert a statement as a
# verified fact. The service uses the EnrichmentPlannerService to deconstruct the
# fact and extract key concepts, ensuring the new knowledge is properly integrated
# into the memory graph.

import json
from typing import Set, TYPE_CHECKING, Dict

from services.base import CognitiveService
from events import Task, Report, LinkDirective
from logger import logger
from utils.reporting import create_report_meta

if TYPE_CHECKING:
    from orchestrator import Orchestrator
    from memory.memory_core import UniversalMemory


class FactIngestionService(CognitiveService):
    def __init__(self, orchestrator: "Orchestrator", memory: "UniversalMemory"):
        super().__init__("FactIngestionService", orchestrator, memory)

    def get_supported_tasks(self) -> Set[str]:
        return {"ingest_fact"}

    async def handle_task(self, task: Task) -> Report:
        """
        Handles the `ingest_fact` task.

        The process involves several steps:
        1.  **Deconstruction**: It cleverly re-uses the `EnrichmentPlannerService` to
            analyze the fact text and extract relevant concepts. This avoids duplicating
            concept extraction logic.
        2.  **Recording**: It creates a `FactNode` with a `VERIFIED` status and a
            `UserImpulse` node to represent the original command for traceability.
        3.  **Integration**: It links the new `FactNode` to the concepts extracted in step 1,
            embedding the new knowledge into the existing graph.
        4.  **Acknowledgement**: It returns a report with a hint for the SynthesisService
            to generate a natural language confirmation for the user.
        """
        fact_text = task.payload.get("fact_text")
        if not fact_text:
            return Report(
                status="FAILURE",
                data={"error": "Fact text is empty"},
                **self._report_meta(task),
            )

        logger.info(
            self.service_name, "Starting fact ingestion...", {"fact": fact_text}
        )

        # Step 1: Deconstruct the fact to extract concepts.
        # We reuse the EnrichmentPlannerService for this by treating the fact as a user impulse.
        # This is an efficient way to ensure consistent concept extraction across the system.
        plan_task = Task(
            type="create_enrichment_plan",
            payload={"original_impulse": fact_text, "instinctive_response": ""},
        )

        plan_report = await self._orchestrator.execute_single_task(plan_task)

        # Step 2: Record the fact and its source command into memory.
        # The fact is immediately marked as VERIFIED.
        parent_impulse_id = self._memory.record_entry(
            node_type="UserImpulse", content=f"!fact {fact_text}"
        )

        fact_node_id = self._memory.record_entry(
            node_type="FactNode",
            content=fact_text,
            attributes={"verification_status": "VERIFIED"},
        )

        if fact_node_id and parent_impulse_id:
            self._memory.graph.add_edge(
                fact_node_id, parent_impulse_id, label="SOURCED_FROM"
            )

        # Step 3: Link the new FactNode to the extracted concepts.
        if fact_node_id and plan_report.status == "SUCCESS":
            queries = plan_report.data.get("queries", [])
            all_concepts = set()
            for query_data in queries:
                concepts_in_query = query_data.get("concepts", [])
                for concept in concepts_in_query:
                    all_concepts.add(concept.lower().strip())

            if all_concepts:
                logger.info(
                    self.service_name,
                    "Linking fact to its deconstructed concepts.",
                    {"concepts": list(all_concepts)},
                )
                for concept_name in all_concepts:
                    if concept_name:
                        concept_id = self._memory.get_or_create_concept_node(
                            concept_name
                        )
                        if concept_id:
                            self._memory.graph.add_edge(
                                fact_node_id, concept_id, label="CONTAINS_CONCEPT"
                            )

        # Step 4: Return a special "Acknowledge" report.
        # This signals the Orchestrator to trigger the SynthesisService to generate
        # a natural language confirmation message.
        report_data = {
            "status": "Acknowledge",
            "hint": f"User provided a fact: '{fact_text}'",
        }
        return Report(status="SUCCESS", data=report_data, **create_report_meta(task))
