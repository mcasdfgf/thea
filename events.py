# events.py: Defines the core data structures for communication within the architecture.
# These dataclasses act as standardized "messages" passed between the Orchestrator
# and the Cognitive Services, ensuring type safety and clear intent.

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import uuid


def generate_correlation_id() -> str:
    """Generates a unique ID to trace a chain of related operations across services."""
    return str(uuid.uuid4())


@dataclass
class LinkDirective:
    """
    An instruction for UniversalMemory on how to link a newly created node
    to an existing node in the graph.
    """

    target_id: str
    label: str


@dataclass
class Task:
    """
    Represents a task sent from the Orchestrator to a Cognitive Service.
    It encapsulates the work to be done and the context for it.
    """

    type: str
    payload: Dict[str, Any]
    correlation_id: str = field(default_factory=generate_correlation_id)
    task_id: str = field(default_factory=lambda: f"task_{uuid.uuid4().hex[:12]}")

    link_to: Optional[LinkDirective] = None


@dataclass
class Report:
    """
    Represents a report sent back from a Cognitive Service to the Orchestrator.
    It contains the result of a completed task.
    """

    status: str
    source_task_type: str
    data: Dict[str, Any]
    correlation_id: str
    source_task_id: str

    link_to: Optional[LinkDirective] = None
    report_node_id: Optional[str] = None
