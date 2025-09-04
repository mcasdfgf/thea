# result_analyzer_agent.py: A micro-agent for synthesizing search results.
# This agent takes a user's original question and a list of raw search snippets
# (e.g., from a web search). It uses an LLM to perform two key tasks:
# 1. Synthesize a single, coherent summary that answers the user's question.
# 2. Extract a list of atomic, verifiable facts from that summary, attributing
#    each fact to its source URL. This prepares the information for ingestion
#    into UniversalMemory as structured `FactNode`s.

import json
import re
from typing import Dict, Any, List
from .base_agent import MicroAgent
from llm_interface import LLMInterface
from logger import logger


class ResultAnalyzerAgent(MicroAgent):
    def __init__(self):
        super().__init__()
        self._llm = LLMInterface()
        self.system_prompt = (
            "You are an AI Research Analyst. Your tasks are:\n"
            "1. Analyze provided search snippets to answer the user's original question.\n"
            "2. **If snippets are irrelevant or empty, use your own general knowledge to answer the question.**\n"
            "3. Synthesize a comprehensive summary in Russian.\n"
            "4. Extract a list of atomic, verifiable facts from your summary. For each fact, specify the URL of the source it came from.\n"
            "5. Your output MUST be a single valid JSON object with keys 'summary' (string) and 'facts' (a list of objects, where each object has 'text' and 'source_url' keys)."
        )

    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes search results to generate a summary and extract facts.

        Args:
            data: A dictionary expected to contain:
                - 'original_query' (str): The user's initial question.
                - 'search_results' (List[Dict]): A list of search result objects,
                  each with 'href' and 'body' keys.

        Returns:
            The modified data dictionary with a new key 'analysis_result', containing
            the 'summary' and a list of 'facts'.
        """
        original_query = data.get("original_query", "")
        search_results = data.get("search_results", [])

        context_for_summary = f"Original user question: '{original_query}'\n\n"

        if not search_results:
            context_for_summary += "Search snippets: [No relevant results found. Please answer from your own knowledge.]\n\n"
        else:
            context_for_summary += "Found snippets:\n"
            for i, res in enumerate(search_results, 1):
                context_for_summary += (
                    f"{i}. URL: {res['href']}\nSnippet: {res['body']}\n\n"
                )

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": context_for_summary},
        ]

        response = await self._llm.generate(messages)
        analysis_result = {"summary": "Failed to process search results.", "facts": []}

        try:
            response_text = response.get("text", "{}")
            # Attempt to find and parse a JSON object within the LLM's response.
            # The regex is robust enough to handle cases where the JSON is embedded
            # within markdown code blocks (e.g., ```json ... ```).
            match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if match:
                json_text = (
                    match.group(0).replace("```json", "").replace("```", "").strip()
                )
                analysis_result = json.loads(json_text)
            else:
                # If no JSON is found, fall back to using the entire response as the summary.
                raise json.JSONDecodeError(
                    "No JSON object found in the response", response_text, 0
                )

        except (json.JSONDecodeError, TypeError):
            logger.warning(
                "ResultAnalyzerAgent",
                "Could not parse JSON from response. Using raw text as summary.",
                {"response": response_text},
            )
            analysis_result["summary"] = response_text
            analysis_result["facts"] = []

        if "facts" in analysis_result and isinstance(analysis_result["facts"], list):
            # Normalize the source URL for facts derived from the model's internal knowledge.
            for fact in analysis_result["facts"]:
                if (
                    not fact.get("source_url")
                    or "knowledge" in fact.get("source_url", "").lower()
                ):
                    fact["source_url"] = "internal_knowledge://Self"

        data["analysis_result"] = analysis_result
        return data
