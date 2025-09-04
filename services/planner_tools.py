# planner_tools.py: Defines the Pydantic models used as "tools" for the LLM.
# These models serve as a strict schema for the JSON output that the
# EnrichmentPlannerService expects from the language model. By providing this schema,
# we can force the LLM to generate structured, validatable data.

from typing import List
from pydantic import BaseModel, Field


class MemorySearchQuery(BaseModel):
    """Defines the structure for a single, targeted search query for long-term memory."""

    semantic_query: str = Field(
        ...,
        description="A clear, self-contained search query in Russian, representing a single topic of interest from the user's text.",
    )
    concepts: List[str] = Field(
        ...,
        description="A list of 2-4 key semantic concepts (nouns, entities) in Russian, extracted from this specific query.",
    )


class MemorySearchQueries(BaseModel):
    """
    The top-level tool model that the LLM is instructed to generate.
    It contains a list of all search queries needed to enrich the conversation.
    """

    queries: List[MemorySearchQuery]
