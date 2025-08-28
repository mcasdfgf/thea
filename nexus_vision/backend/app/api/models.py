# file: nexus_vision/backend/app/api/models.py

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# Pydantic models are used by FastAPI for automatic request validation,
# serialization (converting data to JSON), and documentation (in the OpenAPI schema).

# --- Request Models ---
# These models define the structure of the data the API expects to receive from the client.


class GraphFilters(BaseModel):
    """Defines the available filtering options for a graph view."""

    node_types: Optional[List[str]] = Field(
        default=None, description="A list of node types to display."
    )
    start_time: Optional[str] = Field(
        default=None, description="Start of the time range in ISO format."
    )
    end_time: Optional[str] = Field(
        default=None, description="End of the time range in ISO format."
    )
    search_query: Optional[str] = Field(
        default=None,
        description="A search string to filter nodes by content (not yet implemented).",
    )


class GraphViewRequest(BaseModel):
    """The request body for the main graph_view endpoint."""

    # The filters are optional; if null, no filtering is applied.
    filters: Optional[GraphFilters] = None


class AppMetadataRequest(BaseModel):
    """
    The request body for the metadata endpoint.
    Allows fetching metadata for a specific time range.
    """

    start_time: Optional[str] = None
    end_time: Optional[str] = None


# --- Response Models ---
# These models define the structure of the data the API will send back to the client.


class NodeData(BaseModel):
    """The inner 'data' payload for a React Flow node."""

    label: str  # The primary text label for the node (often the type).
    type: str  # The original node type from the memory graph.
    color: str  # The hex color code for the node.
    shape: str  # The shape identifier (e.g., 'circle', 'star').
    size: int  # The diameter or size of the node in pixels.
    full_data: Dict[
        str, Any
    ]  # A dictionary containing all original attributes from the graphml node.


class Node(BaseModel):
    """Defines the structure of a single node object for React Flow."""

    id: str
    data: NodeData
    # NOTE: This is a fixed value for React Flow to use our custom rendering component.
    type: str = "customNode"


class Edge(BaseModel):
    """Defines the structure of a single edge object for React Flow."""

    id: str
    source: str  # The ID of the source node.
    target: str  # The ID of the target node.
    label: Optional[str] = None  # The text label to display on the edge.
    type: Optional[str] = None  # The edge type (e.g., 'default', 'dashed') for styling.
    # A container for additional data, like the text for the edge label.
    data: Optional[Dict[str, Any]] = None


class GraphViewResponse(BaseModel):
    """The response body for endpoints that return a graph structure."""

    nodes: List[Node]
    edges: List[Edge]


class AppMetadata(BaseModel):
    """
    The response body for the metadata endpoint.
    Provides all the necessary information for the frontend to initialize its UI controls.
    """

    all_node_types: List[str]  # A list of all unique node types found in the graph.
    min_timestamp: Optional[str]  # The earliest timestamp found in the graph.
    max_timestamp: Optional[str]  # The latest timestamp found in the graph.
    node_type_counts: Dict[
        str, int
    ]  # A count of nodes for each type *within the selected time range*.
    total_counts_all_time: Dict[
        str, int
    ]  # A count of nodes for each type across the *entire* graph.
