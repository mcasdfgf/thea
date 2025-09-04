# reflection_service.py: A service for the "slow" cognitive loop that performs
# high-level synthesis of knowledge. Its primary function is to analyze the entire
# corpus of existing insights (`KnowledgeCrystalNode`s) to find recurring patterns.
# When multiple insights about the same topic are found, it merges them into a single,
# stronger, and more generalized insight, effectively "verifying" and evolving the
# system's knowledge base.

import json
import asyncio
from typing import Set, TYPE_CHECKING, List, Dict, Tuple
from prompts.service_prompts import REFLECTION_PROMPT_TEMPLATE
from collections import defaultdict
import networkx as nx

from services.base import CognitiveService
from events import Task, Report
from logger import logger
from llm_interface import LLMInterface
from utils.reporting import create_report_meta

if TYPE_CHECKING:
    from orchestrator import Orchestrator
    from memory.memory_core import UniversalMemory


class ReflectionService(CognitiveService):
    def __init__(self, orchestrator: "Orchestrator", memory: "UniversalMemory"):
        super().__init__("ReflectionService", orchestrator, memory)
        self._llm = LLMInterface()

    def get_supported_tasks(self) -> Set[str]:
        return {"run_deep_reflection"}

    async def _synthesize_insights_within_clusters(
        self, clusters: Dict[str, List[str]]
    ) -> List[Dict]:
        """
        Implements the core logic for insight synthesis and strengthening.

        This process follows the "Actuality + Strength" model:
        1.  It finds all currently "active" insights in memory.
        2.  It groups them by their shared topic (a sorted pair of concepts).
        3.  For any topic with two or more active insights, it triggers a merge operation.
        4.  During a merge, it uses an LLM to generate a new, more general insight.
        5.  The new insight inherits the summed "strength" of its predecessors.
        6.  The old insights are marked as "inactive" (`active_status` = 0), effectively
            being superseded by the new, stronger one.
        """
        logger.info(
            self.service_name,
            "Level 3 Synthesis: Strengthening insights using 'Actuality+Strength' model...",
        )

        active_insights_by_topic = defaultdict(list)
        for node_id, data in self._memory.graph.nodes(data=True):
            if (
                data.get("type") == "KnowledgeCrystalNode"
                and int(data.get("active_status", 0)) == 1
            ):
                concepts_str = data.get("source_concepts", "")
                if concepts_str:
                    try:
                        topic_list = sorted(
                            [c.strip() for c in concepts_str.split(",")]
                        )
                        if len(topic_list) == 2:
                            topic = tuple(topic_list)
                            insight_data = data.copy()
                            insight_data["id"] = node_id
                            active_insights_by_topic[topic].append(insight_data)
                    except Exception as e:
                        logger.warning(
                            self.service_name,
                            f"Could not process concepts for insight {node_id}",
                            {"concepts": concepts_str, "error": str(e)},
                        )

        topics_to_merge = {
            topic: insights
            for topic, insights in active_insights_by_topic.items()
            if len(insights) >= 2
        }

        if not topics_to_merge:
            logger.info(
                self.service_name, "No active insights found eligible for merging."
            )
            return []

        logger.info(
            self.service_name,
            f"Found {len(topics_to_merge)} topics for insight strengthening.",
        )

        newly_created_insights = []
        for topic, insights_to_merge in topics_to_merge.items():

            new_content = await self._generate_verified_insight(
                topic, insights_to_merge
            )

            new_strength = sum(
                int(insight.get("strength", 1)) for insight in insights_to_merge
            )

            new_crystal_id = self._memory.record_entry(
                node_type="KnowledgeCrystalNode",
                content=new_content,
                attributes={
                    "source_concepts": ", ".join(topic),
                    "active_status": 1,
                    "strength": new_strength,
                },
            )

            if new_crystal_id:
                for concept_name in topic:
                    concept_id = self._memory.get_or_create_concept_node(concept_name)
                    if concept_id:
                        self._memory.graph.add_edge(
                            new_crystal_id, concept_id, label="INSIGHT_FROM_CONCEPT"
                        )

                for old_insight in insights_to_merge:
                    if self._memory.graph.has_node(old_insight["id"]):
                        self._memory.graph.nodes[old_insight["id"]]["active_status"] = 0

                newly_created_insights.append(
                    {
                        "topic": topic,
                        "new_insight_id": new_crystal_id,
                        "new_strength": new_strength,
                        "merged_count": len(insights_to_merge),
                    }
                )

        logger.info(
            self.service_name,
            "Synthesis and strengthening process completed.",
            {"created_count": len(newly_created_insights)},
        )
        return newly_created_insights

    async def _generate_verified_insight(
        self, pair: Tuple[str, str], weak_insights: List[Dict]
    ) -> str:
        """
        Uses an LLM to generalize and merge multiple weak insights into a single, strong one.
        """
        insight_texts = "\n- ".join([f"\"{w.get('content')}\"" for w in weak_insights])
        system_prompt = REFLECTION_PROMPT_TEMPLATE
        user_content = (
            f"Concepts: {pair[0]}, {pair[1]}\n"
            f"Micro-insights from different dialogues:\n- {insight_texts}\n\n"
            f"Your Task: Formulate a single, unified, and verified insight in Russian based on the provided evidence."
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]
        response = await self._llm.generate(messages, temperature=0.5)
        return response.get("text", f"Failed to generalize insights for {pair}.")

    async def handle_task(self, task: Task) -> Report:
        """
        Handles the `run_deep_reflection` task.
        This is the main entry point for the service, triggering the full
        synthesis and strengthening cycle.
        """
        logger.info(self.service_name, "Starting full deep reflection cycle...")

        verified_insights_report = await self._synthesize_insights_within_clusters({})

        report_data = {
            "message": "Deep reflection cycle completed.",
            "details": {"level_3_verified_insights": verified_insights_report},
        }

        self._memory.close()
        logger.info(
            self.service_name, "Automatic save triggered after deep reflection cycle."
        )

        return Report(status="SUCCESS", data=report_data, **create_report_meta(task))
