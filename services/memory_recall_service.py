# memory_recall_service.py: The core information retrieval engine of the architecture.
# This service implements a sophisticated hybrid search and ranking pipeline to find
# the most relevant pieces of information in UniversalMemory. It combines semantic
# search, graph-based conceptual search, and multi-factor relevance scoring.

import asyncio
from typing import Set, TYPE_CHECKING, Any, Dict, List

from services.base import CognitiveService
from events import Task, Report, LinkDirective
from logger import logger
from config import RECALL_RANKING_CONFIG, ALLOWED_NODE_TYPES_FOR_RECALL
from .micro_agents.reranker_agent import RerankerAgent
from utils.reporting import create_report_meta

if TYPE_CHECKING:
    from orchestrator import Orchestrator
    from memory.memory_core import UniversalMemory


class MemoryRecallService(CognitiveService):
    def __init__(self, orchestrator: "Orchestrator", memory: "UniversalMemory"):
        super().__init__("MemoryRecallService", orchestrator, memory)
        self.reranker_agent = RerankerAgent()

    def get_supported_tasks(self) -> Set[str]:
        return {"recall_request"}

    async def handle_task(self, task: Task) -> Report:
        """
        Handles the `recall_request` task, orchestrating the full search pipeline.

        The pipeline consists of three main stages:
        1.  **Recall**: A wide, parallel search using both semantic (vector) and
            conceptual (graph) methods to gather a large pool of potential candidates.
        2.  **Rank**: A mechanical ranking algorithm that scores candidates based on a
            multi-factor configuration (see `RECALL_RANKING_CONFIG`), considering
            how they were found (semantic similarity, concept intersections, etc.).
        3.  **Finalize**: Selects the top N candidates after ranking to be sent to
            the SynthesisService. A reranking step (commented out) can be added here
            for finer-grained relevance scoring.
        """
        payload = task.payload.get("request_payload", {})
        semantic_query = payload.get("semantic_query", "")
        concepts = payload.get("concepts", [])

        logger.info(
            self.service_name,
            "Recall request received",
            {"semantic_query": semantic_query, "concepts": concepts},
        )

        if not concepts and not semantic_query:
            return Report(
                status="SUCCESS", data={"found_nodes": []}, **create_report_meta(task)
            )

        logger.info(self.service_name, "Starting Recall->Rank pipeline...")

        # --- Stage 1: RECALL (Hybrid Search) ---
        # Perform semantic and conceptual searches in parallel to gather initial candidates.
        semantic_task = asyncio.create_task(self._semantic_capture(semantic_query))
        conceptual_task = asyncio.create_task(self._conceptual_capture(concepts))
        semantic_candidates, conceptual_candidates = await asyncio.gather(
            semantic_task, conceptual_task
        )

        logger.info(
            self.service_name,
            "Hybrid search results (before merging)",
            {
                "semantic_candidates_count": len(semantic_candidates),
                "conceptual_candidates_count": len(conceptual_candidates),
            },
        )

        candidate_pool = self._build_candidate_pool(
            semantic_candidates, conceptual_candidates
        )
        mechanically_ranked_candidates = self._rank_candidates(candidate_pool)

        recall_limit = RECALL_RANKING_CONFIG.get("recall", {}).get("recall_limit", 20)
        candidates_for_rerank = mechanically_ranked_candidates[:recall_limit]

        log_data_ranked = [
            {
                "id": c.get("id", "N/A")[:8],
                "type": c.get("type"),
                "score": round(c.get("relevance_score", 0), 2),
                "content_preview": str(c.get("content", ""))[:60].replace("\n", " ")
                + "...",
            }
            for c in candidates_for_rerank
        ]
        logger.info(
            self.service_name,
            f"Top {len(candidates_for_rerank)} candidates after mechanical ranking (pre-reranker)",
            log_data_ranked,
        )

        if not candidates_for_rerank:
            return Report(
                status="SUCCESS", data={"found_nodes": []}, **create_report_meta(task)
            )

        # --- Stage 2: RANK (Multi-Factor Scoring) ---
        # Merge candidates and apply the mechanical ranking algorithm from the config.
        # reranker_input = {
        #     "query": semantic_query,
        #     "candidates": candidates_for_rerank
        # }
        # reranker_output = await self.reranker_agent.process(reranker_input)
        # reranked_candidates = reranker_output.get('reranked_candidates', [])

        reranked_candidates = candidates_for_rerank
        logger.info(
            self.service_name,
            "Reranker skipped. Using mechanically ranked results.",
        )

        # --- Stage 3: FINALIZE (Select Top N) ---
        # Select the best candidates to form the final memory package.
        # NOTE: A cross-encoder reranking step is currently disabled for performance.
        # It can be re-enabled here for higher accuracy at the cost of latency.
        final_top_n = RECALL_RANKING_CONFIG.get("recall", {}).get("final_top_n", 5)
        final_candidates = reranked_candidates[:final_top_n]

        log_data_final = [
            {
                "id": c.get("id", "N/A")[:8],
                "type": c.get("type"),
                "score": round(c.get("relevance_score", 0), 3),
                "content_preview": str(c.get("content", ""))[:60].replace("\n", " ")
                + "...",
            }
            for c in final_candidates
        ]
        logger.info(
            self.service_name,
            f"Top {len(final_candidates)} final candidates after ranking",
            log_data_final,
        )

        if final_candidates:
            top_ids = [c.get("id", "N/A")[:8] for c in final_candidates]
            top_scores = [
                f"{c.get('relevance_score', 0):.3f}" for c in final_candidates
            ]
            logger.info(
                self.service_name,
                "Ranking complete.",
                {"top_ids": top_ids, "top_scores": top_scores},
            )

        report_data = {
            "found_nodes": final_candidates,
            "source_node_ids": [node.get("id", "N/A") for node in final_candidates],
        }

        return Report(status="SUCCESS", data=report_data, **create_report_meta(task))

    async def _semantic_capture(self, query: str) -> Dict[str, float]:
        """Flow A: Performs a broad semantic search across multiple vector collections."""
        if not query:
            return {}

        top_k = RECALL_RANKING_CONFIG.get("recall", {}).get("semantic_top_k", 50)

        where_filter = {"type": {"$in": ALLOWED_NODE_TYPES_FOR_RECALL}}

        all_ids, all_scores = [], []
        for collection_name in ["experience", "insight"]:
            ids, scores = self._memory.vector_store.search(
                collection_name, query, k=top_k, where_filter=where_filter
            )
            all_ids.extend(ids)
            all_scores.extend(scores)

        return dict(zip(all_ids, all_scores))

    async def _conceptual_capture(
        self, concepts: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """Flow B: Performs a graph-based search, finding nodes directly linked to the given concepts."""
        if not concepts:
            return {}

        candidate_intersections: Dict[str, Dict[str, Any]] = {}

        for concept_name in concepts:
            concept_node = self._memory.get_node_by_attribute("content", concept_name)
            if not (concept_node and concept_node.get("type") == "ConceptNode"):
                continue

            neighbors = list(self._memory.graph.predecessors(concept_node["id"]))
            for neighbor_id in neighbors:
                neighbor_data = self._memory.graph.nodes[neighbor_id]

                if neighbor_data.get("type") not in ALLOWED_NODE_TYPES_FOR_RECALL:
                    continue

                if neighbor_id not in candidate_intersections:
                    candidate_intersections[neighbor_id] = {
                        "node_data": neighbor_data,
                        "intersections": 0,
                    }

                candidate_intersections[neighbor_id]["intersections"] += 1

        return candidate_intersections

    def _build_candidate_pool(self, semantic_dict, conceptual_dict):
        """Merges results from semantic and conceptual searches into a unified pool for ranking."""
        pool = {}

        for node_id, data in conceptual_dict.items():
            pool[node_id] = {
                "node_data": data["node_data"],
                "score": 0,
                "found_by": {
                    "semantic": 0.0,
                    "conceptual": data["intersections"],
                    "associative": False,
                },
            }
            pool[node_id]["node_data"]["id"] = node_id

        for node_id, score in semantic_dict.items():
            if node_id not in pool:
                node_data = self._memory.graph.nodes.get(node_id, {})
                if not node_data:
                    continue

                if node_data.get("type") not in ALLOWED_NODE_TYPES_FOR_RECALL:
                    continue

                pool[node_id] = {
                    "node_data": node_data,
                    "score": 0,
                    "found_by": {
                        "semantic": score,
                        "conceptual": 0,
                        "associative": False,
                    },
                }
                pool[node_id]["node_data"]["id"] = node_id
            else:
                pool[node_id]["found_by"]["semantic"] = score

        return pool

    def _rank_candidates(self, candidate_pool: Dict) -> List[Dict]:
        """
        Applies the multi-factor scoring algorithm defined in `RECALL_RANKING_CONFIG`.
        This is the core of the mechanical ranking stage, where each candidate gets a
        relevance score based on how and where it was found.
        """
        weights = RECALL_RANKING_CONFIG.get("weights", {})
        ranked_list = []

        for node_id, data in candidate_pool.items():
            score = 0
            found_by = data["found_by"]

            score += found_by["semantic"] * weights.get(
                "semantic_similarity_multiplier", 15
            )
            score += found_by["conceptual"] * weights.get(
                "conceptual_intersection_bonus", 10
            )
            if found_by["associative"]:
                score += weights.get("associative_chain_bonus", 20)

            if found_by["semantic"] > 0 and found_by["conceptual"] > 0:
                score += weights.get("cross_validation_bonus", 40)

            if data["node_data"].get("type") == "UserImpulse":
                score *= 0.7

            node_data_copy = data["node_data"].copy()
            node_data_copy["id"] = node_id
            node_data_copy["relevance_score"] = score
            ranked_list.append(node_data_copy)

        ranked_list.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        return ranked_list
