# file: nexus_vision/backend/app/api/endpoints/graph.py

from fastapi import APIRouter, HTTPException, Body
import networkx as nx

# --- Application-specific imports ---
# Singleton instance to safely access the loaded graph.
from app.core.graph_loader import graph_loader

# The service layer that contains all the business logic for graph processing.
from app.services.graph_service import GraphService, COLOR_PALETTE, SHAPE_MAP

# Pydantic models for request and response validation.
from app.api.models import (
    GraphViewRequest,
    GraphViewResponse,
    AppMetadata,
    AppMetadataRequest,
)

# Create a new router for graph-related endpoints.
router = APIRouter()
# Create an instance of the service to handle the logic.
graph_service = GraphService()


@router.post("/graph_view", response_model=GraphViewResponse)
async def get_graph_view(request: GraphViewRequest = Body(...)):
    """
    The main endpoint for fetching a filtered and processed view of the graph.
    It takes a set of filters and returns a graph structure formatted for React Flow.
    """
    # Safely get the current state of the graph from the loader.
    graph = await graph_loader.get_graph()
    if not isinstance(graph, nx.DiGraph):
        # Return a 503 Service Unavailable error if the graph file isn't loaded.
        raise HTTPException(
            status_code=503,
            detail="Graph is not loaded or currently being reloaded. Please try again.",
        )

    # Delegate all the complex processing logic to the service layer.
    processed_view = graph_service.process_graph_view(graph, request.filters)
    return processed_view


@router.post("/metadata", response_model=AppMetadata)
async def get_metadata(request: AppMetadataRequest):
    """
    Returns metadata for initializing the UI, such as available node types,
    time ranges, and node counts, potentially filtered by a time range.
    """
    graph = await graph_loader.get_graph()
    if not isinstance(graph, nx.DiGraph):
        raise HTTPException(
            status_code=503, detail="Graph is not loaded or currently being reloaded."
        )

    # Delegate the metadata calculation to the service layer.
    metadata = graph_service.get_app_metadata(
        graph=graph, start_time=request.start_time, end_time=request.end_time
    )
    return metadata


@router.get("/visual_metadata")
async def get_visual_metadata():
    """
    Provides static visual metadata (colors and shapes) for the frontend.
    This allows the frontend to build legends and style elements without
    hardcoding these values.
    """
    # Aggregate color and shape data into a single, convenient structure for the client.
    legend_data = {}
    for node_type, color in COLOR_PALETTE.items():
        if node_type not in legend_data:
            legend_data[node_type] = {}
        legend_data[node_type]["color"] = color

    for node_type, shape in SHAPE_MAP.items():
        if node_type not in legend_data:
            legend_data[node_type] = {}
        legend_data[node_type]["shape"] = shape

    return legend_data


@router.get("/trace_chain/{node_id}", response_model=GraphViewResponse)
async def trace_chain(node_id: str):
    """
    Accepts a node ID and returns the subgraph representing its "cognitive chain".
    This is the backend implementation for the 'trace' feature in the UI.
    """
    graph = await graph_loader.get_graph()
    if not isinstance(graph, nx.DiGraph):
        raise HTTPException(status_code=503, detail="Graph is not loaded.")

    # Delegate the complex tracing logic to the service layer.
    traced_data = graph_service.trace_cognitive_chain(graph, node_id)
    return traced_data
