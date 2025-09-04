# query_optimizer_agent.py: A micro-agent for enhancing search queries.
# This agent takes a single, high-level user question and uses an LLM to
# brainstorm several alternative, keyword-rich query variations. This helps
# to broaden the search scope and increase the chances of finding relevant
# information from external sources.

import json
import re
from typing import Dict, Any, List
from .base_agent import MicroAgent
from llm_interface import LLMInterface
from logger import logger


class QueryOptimizerAgent(MicroAgent):
    def __init__(self):
        super().__init__()
        self._llm = LLMInterface()
        self.system_prompt = (
            "You are a Search Query Optimization Expert. Your task is to transform a user's question "
            "into 3 distinct, keyword-rich search queries. Generate queries in both Russian and English "
            "to maximize coverage. Your output MUST be a single, valid JSON list of simple strings."
        )

    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Takes an original query and generates several optimized variations.

        Args:
            data: A dictionary expected to contain the key 'original_query' (str).

        Returns:
            The modified data dictionary with a new key 'optimized_queries' (List[str]).
        """
        original_query = data.get("original_query", "")
        if not original_query:
            data["optimized_queries"] = []
            return data

        user_prompt = (
            f"Original question: '{original_query}'\n\n"
            f'Generate 3 optimized search queries. Example output: `["query 1", "query 2", "query 3"]`'
        )
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        response = await self._llm.generate(messages)
        optimized_queries = [original_query]

        try:
            response_text = response.get("text", "[]")
            matches = re.findall(r"\[.*?\]", response_text, re.DOTALL)
            processed_queries = []
            for match_str in matches:
                try:
                    queries = json.loads(match_str)
                    if isinstance(queries, list):
                        for item in queries:
                            if isinstance(item, str) and item:
                                processed_queries.append(item)
                            elif isinstance(item, dict) and "query" in item:
                                processed_queries.append(item["query"])
                except json.JSONDecodeError:
                    continue

            if processed_queries:
                optimized_queries = list(dict.fromkeys(processed_queries))
                logger.info(
                    "QueryOptimizerAgent",
                    "Optimized search queries generated.",
                    {"queries": optimized_queries},
                )

        except Exception as e:
            logger.error(
                "QueryOptimizerAgent",
                "Error while processing LLM response.",
                {"error": str(e), "response": response_text},
            )

        data["optimized_queries"] = optimized_queries
        return data
