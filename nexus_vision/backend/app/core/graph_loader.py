# file: nexus_vision/backend/app/core/graph_loader.py

import networkx as nx
import os
import asyncio
from typing import Optional

from .config import settings


class GraphLoader:
    """
    A thread-safe, asynchronous manager for loading and reloading the memory graph file.

    This class ensures that the graph is loaded only once and is reloaded automatically
    if the source file changes on disk. It uses an asyncio.Lock to prevent race
    conditions when multiple requests try to access the graph during a reload.
    """

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.graph: Optional[nx.DiGraph] = None
        # Stores the last modification time of the file to detect changes.
        self._last_mtime: float = 0
        # An asyncio lock to ensure atomic read/write operations on the graph object.
        self._lock = asyncio.Lock()

    async def load_graph(self):
        """
        Loads the graph from the .graphml file if it has been modified.
        This method is designed to be called periodically.
        """
        try:
            # Check the file's last modification time to avoid unnecessary reads.
            current_mtime = os.path.getmtime(self.file_path)
            if current_mtime > self._last_mtime:
                # Acquire the lock to prevent other tasks from reading a partially loaded graph.
                async with self._lock:
                    # Double-check the condition inside the lock to avoid race conditions.
                    # Another task might have already loaded the graph while this one was waiting for the lock.
                    if current_mtime > self._last_mtime:
                        print(
                            f"[{self.__class__.__name__}] Graph file has changed. Reloading..."
                        )
                        self.graph = nx.read_graphml(self.file_path)
                        self._last_mtime = current_mtime
                        print(
                            f"[{self.__class__.__name__}] Graph loaded successfully. "
                            f"Nodes: {self.graph.number_of_nodes()}, Edges: {self.graph.number_of_edges()}"
                        )
        except FileNotFoundError:
            print(
                f"[{self.__class__.__name__}][ERROR] Graph file not found at: {self.file_path}"
            )
            self.graph = None
        except Exception as e:
            print(f"[{self.__class__.__name__}][ERROR] Failed to load graph: {e}")
            self.graph = None

    async def get_graph(self) -> Optional[nx.DiGraph]:
        """

        Safely returns the current version of the graph.

        Returns:
            A copy of the networkx graph object, or None if the graph is not loaded.
            Returning a copy ensures that downstream modifications do not affect the original object.
        """
        async with self._lock:
            return self.graph.copy() if self.graph else None


# --- Singleton Instance ---
# This creates a single, shared instance of the GraphLoader that will be used
# across the entire application. This is a common pattern for managing shared resources.
graph_loader = GraphLoader(settings.GRAPH_FILE_PATH)


async def periodic_graph_reload():
    """

    The background task that runs for the application's entire lifespan.
    It periodically triggers the graph loader to check for file updates.
    """
    while True:
        await graph_loader.load_graph()
        # The check interval can be adjusted depending on the expected frequency of updates.
        await asyncio.sleep(3)  # Checks for updates every 3 seconds.
