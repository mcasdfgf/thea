# base_agent.py: Defines the abstract base class for all micro-agents.
# Micro-agents are small, focused components designed to be chained together in a pipeline.
# Each agent performs a single, specific transformation on a shared data dictionary.

from abc import ABC, abstractmethod
from typing import Dict, Any


class MicroAgent(ABC):
    """
    Abstract base class for a single-purpose agent in a processing pipeline.
    Each agent takes a data dictionary, performs its specific task, and returns
    the modified dictionary for the next agent in the chain.
    """

    def __init__(self):
        pass

    @abstractmethod
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        The main method that executes the agent's logic.

        Args:
            data: The dictionary containing the current state of the data being processed.

        Returns:
            The modified data dictionary.
        """
        pass
