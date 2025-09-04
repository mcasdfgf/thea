# memory_core.py: Implements the UniversalMemory, the central knowledge repository.
# This module orchestrates the four layers of memory:
# 1.  Symbolic Layer (Graph): A networkx graph for explicit relationships.
# 2.  Semantic Layer (Vector Store): A vector database for contextual similarity search.
# 3.  Temporal Layer (Time Store): A chronological log of all events.
# 4.  Conceptual Layer (Implicit): Formed by `ConceptNode`s within the graph.
# It ensures that every piece of experience is recorded transactionally across all layers.

import yaml
import networkx as nx
import os
import json
from .vector_store import VectorStore
from .time_store import TimeStore
from config import CHRONICLE_FILE_PATH
from logger import logger


class Schema:
    def __init__(self, schema_path):
        with open(schema_path, "r", encoding="utf-8") as f:
            self.data = yaml.safe_load(f)
        self.node_types = self.data.get("node_types", {})
        self.edge_types = self.data.get("edge_types", {})
        logger.info("Schema", "Memory schema loaded successfully.")

    def validate_node(self, node_type, attributes):
        if node_type not in self.node_types:
            return False
        return True

    def validate_edge(self, source_type, target_type, edge_label):
        return True


class UniversalMemory:
    def __init__(self, schema_path: str, snapshot_path: str = "memory_core.graphml"):
        self.schema = Schema(schema_path)
        self.snapshot_path = snapshot_path

        self.graph = self._load_graph_snapshot()
        logger.info("MemoryCore", "Symbolic Layer (NetworkX) initialized.")

        self.vector_store = VectorStore()

        self.time_store = TimeStore(chronicle_path=CHRONICLE_FILE_PATH)
        logger.info("MemoryCore", "Temporal Layer initialized.")

        logger.info("\n--- UniversalMemory is ready ---")

    def _load_graph_snapshot(self) -> nx.DiGraph:
        """Loads the graph state from a GraphML file if it exists."""
        if os.path.exists(self.snapshot_path):
            logger.info(
                "MemoryCore",
                f"Found graph snapshot. Loading from {self.snapshot_path}...",
            )
            try:
                return nx.read_graphml(self.snapshot_path)
            except Exception as e:
                logger.error(
                    "MemoryCore",
                    f"Error loading graph: {e}. Creating a new, empty graph.",
                )
                return nx.DiGraph()
        else:
            logger.warning(
                "MemoryCore", "Graph snapshot not found. Creating a new, empty graph."
            )
            return nx.DiGraph()

    def close(self):
        """Persists all memory components to disk."""
        self.save_snapshot()
        self.time_store.save_chronicle()
        logger.info("MemoryCore", "All memory components have been persisted.")

    def save_snapshot(self, path: str = None):
        """Saves the current state of the symbolic graph to a GraphML file."""
        save_path = path or self.snapshot_path
        try:
            # GraphML requires attributes to be primitive types (str, int, float, bool).
            # This loop iterates through all nodes and edges to serialize complex
            # attributes (like dicts or lists) into JSON strings before saving.
            for node_id, data in self.graph.nodes(data=True):
                for key, value in data.items():
                    if not isinstance(value, (str, int, float, bool)):
                        self.graph.nodes[node_id][key] = json.dumps(
                            value, ensure_ascii=False, default=str
                        )
                    elif not isinstance(value, str):
                        self.graph.nodes[node_id][key] = str(value)

            for u, v, data in self.graph.edges(data=True):
                for key, value in data.items():
                    if not isinstance(value, (str, int, float, bool)):
                        self.graph.edges[u, v][key] = json.dumps(
                            value, ensure_ascii=False, default=str
                        )
                    elif not isinstance(value, str):
                        self.graph.edges[u, v][key] = str(value)

            nx.write_graphml(self.graph, save_path)
            logger.info(
                "MemoryCore",
                f"Symbolic graph snapshot successfully saved to {save_path}",
            )
        except Exception as e:
            logger.error(
                "MemoryCore",
                "Error saving graph snapshot.",
                {"error": str(e)},
                exc_info=True,
            )

    def get_node_by_attribute(self, attribute_name: str, attribute_value: str):
        """Finds a concept node by its name or creates a new one if it doesn't exist."""
        for node_id, data in self.graph.nodes(data=True):
            if data.get(attribute_name) == attribute_value:
                node_data = data.copy()
                node_data["id"] = node_id
                return node_data
        return None

    def get_or_create_concept_node(self, concept_name: str):
        """Finds a concept node by its name or creates a new one if it doesn't exist."""
        existing = self.get_node_by_attribute("content", concept_name)
        if existing and existing.get("type") == "ConceptNode":
            return existing["id"]

        return self.record_entry(node_type="ConceptNode", content=concept_name)

    def record_entry(
        self, node_type: str, content: any, attributes: dict = None, links: list = None
    ):
        """
        The main transactional entry point for recording experience into memory.
        It coordinates writing a new node and its relationships to all memory layers.
        """
        logger.info(
            "MemoryCore", f"Received request to record a new node", {"type": node_type}
        )

        attributes = attributes or {}
        links = links or []

        if not self.schema.validate_node(node_type, attributes):
            logger.error(
                "MemoryCore", f"Node failed schema validation", {"type": node_type}
            )
            return None

        # 1. Get a unique, timestamped ID from the TimeStore
        node_id, timestamp = self.time_store.get_new_timestamped_id()

        # 2. Prepare node attributes for the graph
        if isinstance(content, (dict, list)):
            # Serialize complex content (dicts, lists) into a JSON string.
            # default=str handles non-serializable types like datetime.
            content_str = json.dumps(content, ensure_ascii=False, default=str)
        else:
            # Ensure simple content is also a string.
            content_str = str(content)

        node_attributes = {
            "type": node_type,
            "content": content_str,
            "timestamp": timestamp.isoformat(),
            **(attributes or {}),
        }

        # 3. Perform the transactional write to all layers
        # 3a. Write to Symbolic Layer (Graph)
        self.graph.add_node(node_id, **node_attributes)
        for link in links:
            if link and hasattr(link, "target_id") and hasattr(link, "label"):
                target_id = link.target_id
                label = link.label

                if self.graph.has_node(target_id):
                    source_type = node_type
                    target_type = self.graph.nodes[target_id].get("type", "Unknown")

                    if self.schema.validate_edge(source_type, target_type, label):
                        self.graph.add_edge(node_id, target_id, label=label)
                    else:
                        logger.warning(
                            "MemoryCore",
                            "Edge validation failed",
                            {"source": source_type},
                        )
                else:
                    logger.warning(
                        "MemoryCore", f"Link target node not found: {target_id}"
                    )

        # 3b. Write to Semantic Layer (Vector Store)
        self.vector_store.add(node_id, node_type, str(content))

        # 3c. Write to Temporal Layer (Time Store)
        self.time_store.record(node_id, timestamp, node_type)

        logger.info(
            "MemoryCore", f"Node '{node_id}' successfully recorded to all layers."
        )
        return node_id
