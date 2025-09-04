# reranker_agent.py: A micro-agent for fine-grained relevance scoring.
# This agent is designed to use a Cross-Encoder model to re-rank a list of
# candidate documents against a specific query. Cross-Encoders are more
# computationally expensive than standard vector search but provide higher accuracy.
#
# NOTE: This agent is currently bypassed in the `MemoryRecallService` for performance
# reasons. The mechanical ranking provides a "good enough" result for the prototype,
# but this agent can be re-enabled for experiments requiring higher precision.

import numpy as np
from typing import Dict, Any, List, Tuple
from .base_agent import MicroAgent
from logger import logger
from config import RERANKER_MODEL_NAME

try:
    from sentence_transformers.cross_encoder import CrossEncoder
except ImportError:
    logger.error(
        "RerankerAgent",
        "The 'sentence-transformers' library is not installed. RerankerAgent will be disabled.",
    )
    CrossEncoder = None


class RerankerAgent(MicroAgent):
    """
    A micro-agent that uses a Cross-Encoder model to re-rank search candidates.
    """

    def __init__(self):
        super().__init__()
        self.model = None
        if CrossEncoder:
            try:
                logger.info("RerankerAgent", f"Loading model: {RERANKER_MODEL_NAME}...")
                self.model = CrossEncoder(RERANKER_MODEL_NAME)
                logger.info("RerankerAgent", "Reranker model loaded successfully.")
            except Exception as e:
                logger.error(
                    "RerankerAgent",
                    "Failed to load the reranker model.",
                    {"error": str(e)},
                )

    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Re-ranks a list of candidate nodes based on their relevance to a query.

        Args:
            data: A dictionary expected to contain:
                - 'query' (str): The search query.
                - 'candidates' (List[Dict]): A list of candidate nodes, each with a 'content' key.

        Returns:
            The modified data dictionary with 'reranked_candidates', a list of the same
            nodes sorted by their new cross-encoder relevance scores.
        """
        query = data.get("query")
        candidates = data.get("candidates", [])

        if not self.model:
            logger.warning(
                "RerankerAgent",
                "Model not loaded. Bypassing reranking and returning original candidates.",
            )
            data["reranked_candidates"] = candidates
            return data

        if not query or not candidates:
            data["reranked_candidates"] = []
            return data

        sentence_pairs = [(query, str(node.get("content", ""))) for node in candidates]

        logger.info(
            "RerankerAgent",
            f"Sending {len(sentence_pairs)} pairs to the cross-encoder model.",
        )

        raw_scores = self.model.predict(sentence_pairs)

        def sigmoid(x):
            return 1 / (1 + np.exp(-x))

        normalized_scores = sigmoid(raw_scores)

        for i, node in enumerate(candidates):
            node["relevance_score"] = float(normalized_scores[i])

        candidates.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

        data["reranked_candidates"] = candidates
        return data
