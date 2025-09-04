# file: nexus_vision/backend/app/services/graph_service.py

import networkx as nx
from typing import List, Dict, Any, Optional
import json
from datetime import datetime, timezone
from collections import Counter, deque

from ..api.models import GraphFilters

# --- Visual Styling Constants ---
# These dictionaries define the visual appearance of nodes in the frontend.
# Centralizing them here allows for easy theme changes without touching frontend code.

COLOR_PALETTE = {
    # Dialogue Nodes (shades of blue)
    "UserImpulse": "#5DADE2",
    "InstinctiveResponseNode": "#85C1E9",
    "FinalResponseNode": "#1B4F72",
    # Process Nodes (shades of yellow/teal)
    "TaskNode": "#FAD7A0",
    "ReportNode": "#F5B041",
    "SearchPlanNode": "#48C9B0",
    # Knowledge Nodes (shades of green)
    "ConceptNode": "#D5F5E3",
    "FactNode": "#A9DFBF",
    "KnowledgeCrystalNode": "#1D8348",
    "ConversationSummaryNode": "#9B59B6",  # (purple)
    # Thematic & Archived Nodes
    "ThemeNode": "#E74C3C",  # (red)
    "ARCHIVED": "#CB4335",  # Special color for archived state
    # Default color for any un-themed node type
    "DEFAULT": "#D5D8DC",
}

SHAPE_MAP = {
    "UserImpulse": "circle",
    "InstinctiveResponseNode": "circle",
    "FinalResponseNode": "circle",
    "KnowledgeCrystalNode": "star",
    "ConceptNode": "triangle",
    "FactNode": "box",
    "SearchPlanNode": "box",
    "ConversationSummaryNode": "database",
    "DEFAULT": "dot",
}

SIZE_MAP = {
    "UserImpulse": 60,
    "FinalResponseNode": 60,
    "InstinctiveResponseNode": 50,
    "ConceptNode": 30,
    "KnowledgeCrystalNode": 80,
    "ThemeNode": 120,  # Themes are major hubs
    "ConversationSummaryNode": 100,
    "DEFAULT": 45,
}


class GraphService:
    """
    Contains all the business logic for processing, filtering, and formatting
    the memory graph for the frontend visualizer.
    """

    # --- Private Helper Methods ---

    def _is_in_time_range(
        self,
        node_data: Dict[str, Any],
        start_time_str: Optional[str],
        end_time_str: Optional[str],
    ) -> bool:
        """Checks if a node's timestamp falls within a given ISO date string range."""
        if not start_time_str and not end_time_str:
            return True
        node_ts_str = node_data.get("timestamp")
        if not node_ts_str:
            return True  # Nodes without a timestamp are always included for simplicity.
        try:
            # Create timezone-aware datetime objects for comparison.
            # Assume UTC if no timezone is specified.
            start_dt = (
                datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
                if start_time_str
                else datetime.min.replace(tzinfo=timezone.utc)
            )
            end_dt = (
                datetime.fromisoformat(end_time_str.replace("Z", "+00:00"))
                if end_time_str
                else datetime.max.replace(tzinfo=timezone.utc)
            )
            node_dt = datetime.fromisoformat(node_ts_str).replace(tzinfo=timezone.utc)
            return start_dt <= node_dt <= end_dt
        except (ValueError, TypeError):
            return False  # Gracefully handle invalid timestamp formats.

    def _get_node_visuals(self, node_data: Dict[str, Any]) -> Dict[str, Any]:
        """Determines the color, shape, and size for a node based on its type and attributes."""
        node_type = node_data.get("type", "DEFAULT")

        # Get the default visual properties from the predefined maps.
        color = COLOR_PALETTE.get(node_type, COLOR_PALETTE["DEFAULT"])
        shape = SHAPE_MAP.get(node_type, SHAPE_MAP["DEFAULT"])
        size = SIZE_MAP.get(node_type, SIZE_MAP["DEFAULT"])

        # --- Special visual logic for KnowledgeCrystalNode ---
        # This block dynamically adjusts visuals based on the node's active_status and strength.
        if node_type == "KnowledgeCrystalNode":
            try:
                # Attributes from graphml are read as strings, so they must be cast to int.
                is_active = int(node_data.get("active_status", 1))

                if is_active == 0:
                    # --- Archived Insight Styling ---
                    # If the insight is archived (status 0), make it less prominent.
                    # 1. Use the existing color defined for archived nodes.
                    color = COLOR_PALETTE.get("ARCHIVED", "#808080")
                    # 2. Reduce its size by half.
                    size = size // 2
                else:
                    # --- Active Insight Styling ---
                    # If the insight is active (status 1), its size reflects its strength.
                    strength = int(node_data.get("strength", 1))
                    # The size grows with strength, but we cap it to prevent excessively large nodes.
                    size += strength * 2
                    size = min(size, 150)  # Set a maximum visual size for clarity.

            except (ValueError, TypeError):
                # If attributes are missing or invalid, do nothing and fall back to default visuals.
                pass

        return {"color": color, "shape": shape, "size": size}

    # --- Core Service Methods ---

    def trace_cognitive_chain(
        self, graph: nx.DiGraph, start_node_id: str
    ) -> Dict[str, List[Dict]]:
        """
        Finds the full "cognitive chain" connected to a start node and formats it for display.
        This implements the 'trace' functionality.
        """
        # Step 1: Resolve partial ID to full ID.
        full_start_id = None
        if graph.has_node(start_node_id):
            full_start_id = start_node_id
        else:
            for node_id in graph.nodes:
                if node_id.startswith(start_node_id):
                    full_start_id = node_id
                    break

        if not full_start_id:
            return {
                "nodes": [],
                "edges": [],
            }  # Return an empty graph if the node is not found.

        # Step 2: Define which edges represent the "process" flow.
        PROCESS_EDGES = [
            "IS_TASK_FOR",
            "IS_RESULT_OF",
            "CONTAINS_PLAN",
            "WAS_SYNTHESIZED_FROM",
            "IS_RESPONSE_TO",
            "HAS_RESEARCH",
            "USED_QUERY",
            "FOUND_SOURCE",
            "CONTAINS_FACT",
            "SOURCED_FROM",
            "IS_INSTINCT_FOR",
        ]

        # Step 3: Use Breadth-First Search (BFS) to find all connected nodes in the chain.
        # BFS is suitable here as we want to explore the entire connected component.
        chain_node_ids = set()
        queue = deque([full_start_id])
        visited = {full_start_id}

        while queue:
            current_id = queue.popleft()
            chain_node_ids.add(current_id)

            # Explore in both directions (predecessors and successors) along process edges.
            for neighbor_id in list(graph.predecessors(current_id)) + list(
                graph.successors(current_id)
            ):
                edge_data_fwd = graph.get_edge_data(current_id, neighbor_id)
                edge_data_bwd = graph.get_edge_data(neighbor_id, current_id)

                is_process_edge = False
                if edge_data_fwd and edge_data_fwd.get("label") in PROCESS_EDGES:
                    is_process_edge = True
                elif edge_data_bwd and edge_data_bwd.get("label") in PROCESS_EDGES:
                    is_process_edge = True

                if is_process_edge and neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append(neighbor_id)

        # Step 4: Create a subgraph containing only the nodes from the chain.
        # .copy() is important to avoid modifying the original graph object.
        subgraph = graph.subgraph(chain_node_ids).copy()

        # Step 5: Reuse the main processing function to format this subgraph.
        # This is a key architectural choice: tracing is just a special case of viewing a filtered graph.
        return self.process_graph_view(subgraph, filters=None)

    def process_graph_view(
        self, graph: nx.DiGraph, filters: Optional[GraphFilters] = None
    ) -> Dict[str, List[Dict]]:
        """
        The main graph processing method. It filters nodes, creates a subgraph,
        infers edges for clarity, and formats the output for React Flow.
        """
        # Start with all nodes in the provided graph.
        visible_node_ids = set(graph.nodes())

        # --- Step 1: Apply filters to determine which nodes are visible ---
        if filters:
            if filters.start_time or filters.end_time:
                time_filtered_ids = {
                    node_id
                    for node_id, data in graph.nodes(data=True)
                    if self._is_in_time_range(
                        data, filters.start_time, filters.end_time
                    )
                }
                visible_node_ids &= time_filtered_ids  # Intersect sets

            if filters.node_types:
                type_filtered_ids = {
                    node_id
                    for node_id, data in graph.nodes(data=True)
                    if data.get("type") in filters.node_types
                }
                visible_node_ids &= type_filtered_ids  # Intersect sets

        # Create a subgraph containing only the nodes that passed all filters.
        subgraph = graph.subgraph(visible_node_ids).copy()

        # --- Step 2: Infer Edges (a key feature for readability) ---
        # If two visible nodes are connected in the *full* graph via a path of *hidden* nodes,
        # draw a dashed "inferred" edge between them.
        for source_id in visible_node_ids:
            for target_id in visible_node_ids:
                if source_id == target_id or subgraph.has_edge(source_id, target_id):
                    continue
                try:
                    # Find the shortest path in the full, unfiltered graph.
                    path = nx.shortest_path(graph, source=source_id, target=target_id)
                    if (
                        len(path) > 2
                    ):  # A path with more than 2 nodes has intermediate steps.
                        skipped_nodes = path[1:-1]
                        # Add an inferred edge only if ALL intermediate nodes are hidden.
                        if all(node not in visible_node_ids for node in skipped_nodes):
                            subgraph.add_edge(
                                source_id,
                                target_id,
                                label="inferred_link",
                                type="dashed",
                                skipped_nodes=[
                                    {
                                        "id": nid,
                                        "type": graph.nodes[nid].get("type", "N/A"),
                                    }
                                    for nid in skipped_nodes
                                ],
                            )
                except nx.NetworkXNoPath:
                    continue

        # --- Step 3: Format nodes and edges into the React Flow JSON structure ---
        nodes_for_response = []
        for node_id, data in subgraph.nodes(data=True):
            visuals = self._get_node_visuals(data)

            # Attempt to parse the 'content' attribute if it's a JSON string.
            # This makes the data much cleaner for the inspector panel on the frontend.
            try:
                full_data_content = json.loads(data.get("content", "{}"))
            except (json.JSONDecodeError, TypeError):
                full_data_content = data.get("content", "")

            full_data_copy = data.copy()
            full_data_copy["content"] = full_data_content
            full_data_copy["id"] = node_id

            nodes_for_response.append(
                {
                    "id": node_id,
                    "type": "customNode",  # Tells React Flow to use our custom renderer
                    "data": {
                        "id": node_id,
                        "label": f"{data.get('type')}",
                        "type": data.get("type"),
                        "full_data": full_data_copy,
                        **visuals,
                    },
                }
            )

        edges_for_response = []
        for source, target, data in subgraph.edges(data=True):
            edge_type = data.get("type", "default")
            label_text = data.get("label", "")
            edges_for_response.append(
                {
                    "id": f"{edge_type}-{source}-{target}-{label_text}",  # Create a more unique ID
                    "source": source,
                    "target": target,
                    "label": "",  # The label is rendered via custom logic on the frontend
                    "data": {
                        "label_text": label_text,
                        "skipped_nodes": data.get("skipped_nodes"),
                    },
                    "type": edge_type,
                }
            )

        return {"nodes": nodes_for_response, "edges": edges_for_response}

    def get_app_metadata(
        self,
        graph: nx.DiGraph,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Calculates and returns metadata required to initialize the frontend UI.
        This includes lists of node types and counts, filtered by the provided time range.
        """
        # Step 1: Filter nodes by time first, if a range is provided.
        nodes_to_process = [
            data
            for _, data in graph.nodes(data=True)
            if self._is_in_time_range(data, start_time, end_time)
        ]

        # Step 2: Calculate metrics based on the filtered list of nodes.
        all_types = set()
        timestamps = []
        node_type_counts = Counter()

        for data in nodes_to_process:
            node_type = data.get("type")
            if node_type:
                all_types.add(node_type)
                node_type_counts[node_type] += 1

            if "timestamp" in data and data["timestamp"]:
                try:
                    timestamps.append(datetime.fromisoformat(data["timestamp"]))
                except (ValueError, TypeError):
                    continue

        # Step 3: Also calculate total counts across ALL time for reference.
        # This is useful for the UI to show "(15 of 200)" for a node type.
        total_counts_all_time = Counter(
            data.get("type") for _, data in graph.nodes(data=True) if data.get("type")
        )

        return {
            "all_node_types": sorted(list(all_types)),
            "min_timestamp": min(timestamps).isoformat() if timestamps else None,
            "max_timestamp": max(timestamps).isoformat() if timestamps else None,
            "node_type_counts": dict(node_type_counts),
            "total_counts_all_time": dict(total_counts_all_time),
        }
