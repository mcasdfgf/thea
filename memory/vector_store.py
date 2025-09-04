# vector_store.py: The Semantic Layer of UniversalMemory.
# This module provides an interface to a vector database (ChromaDB) for efficient
# semantic similarity searches. It handles text encoding, vector storage in different
# collections, and retrieval of nearest neighbors.

import chromadb
from sentence_transformers import SentenceTransformer
from config import CHROMA_DB_PATH, EMBEDDING_MODEL_NAME
from logger import logger


class VectorStore:
    """
    Manages vector collections for semantic search using ChromaDB and SentenceTransformers.
    """

    def __init__(self):
        logger.info("VectorStore", "Initializing...")
        try:
            self.client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
            logger.info(
                "VectorStore", f"ChromaDB client connected to: {CHROMA_DB_PATH}"
            )

            logger.info(
                "VectorStore", f"Loading embedding model '{EMBEDDING_MODEL_NAME}'..."
            )
            self.encoder = SentenceTransformer(EMBEDDING_MODEL_NAME)
            logger.info("VectorStore", "Embedding model loaded.")

            self.collections = {
                "experience": self.client.get_or_create_collection(
                    name="experience_collection", metadata={"hnsw:space": "cosine"}
                ),
                "concept": self.client.get_or_create_collection(
                    name="concept_collection", metadata={"hnsw:space": "cosine"}
                ),
                "insight": self.client.get_or_create_collection(
                    name="insight_collection", metadata={"hnsw:space": "cosine"}
                ),
            }
            logger.info("VectorStore", "Vector collections are ready.")

        except Exception as e:
            logger.error(
                "VectorStore",
                "Critical initialization error.",
                {"error": str(e)},
                exc_info=True,
            )
            raise

    def _get_collection(self, node_type: str):
        """Determines the appropriate ChromaDB collection for a given node type."""
        if node_type in [
            "UserImpulse",
            "FinalResponseNode",
            "FactNode",
            "ReportNode",
            "QueryNode",
        ]:
            return self.collections["experience"]
        elif node_type == "ConceptNode":
            return self.collections["concept"]
        elif node_type == "KnowledgeCrystalNode":
            return self.collections["insight"]
        return None

    def add(self, node_id: str, node_type: str, text: str):
        """Encodes text and adds or updates its vector in the appropriate collection."""
        collection = self._get_collection(node_type)
        if collection is None or not text.strip():
            return

        try:
            embedding = self.encoder.encode([text], convert_to_tensor=False)[0].tolist()

            collection.upsert(
                ids=[node_id], embeddings=[embedding], metadatas=[{"type": node_type}]
            )
        except Exception as e:
            logger.error(
                "VectorStore",
                f"Error adding/updating vector for node {node_id}",
                {"error": str(e)},
                exc_info=True,
            )

    def search(
        self,
        collection_name: str,
        query_text: str,
        k: int = 5,
        where_filter: dict = None,
    ) -> (list[str], list[float]):
        """
        Searches a collection for the k-nearest neighbors to a query text.

        Args:
        collection_name: The name of the collection to search ('experience', 'concept', etc.).
        query_text: The text to search for.
        k: The number of nearest neighbors to return.
        where_filter: An optional ChromaDB metadata filter.

        Returns:
        A tuple containing a list of node IDs and a list of their corresponding similarity scores.
        """
        if collection_name not in self.collections:
            logger.warning(
                "VectorStore",
                f"Attempted to search in a non-existent collection: {collection_name}",
            )
            return [], []

        collection = self.collections[collection_name]

        try:
            query_embedding = self.encoder.encode(
                [query_text], convert_to_tensor=False
            )[0].tolist()

            # Dynamically build the query arguments to include the `where` filter
            # only when it is provided. This is the modern way to query ChromaDB.
            query_args = {"query_embeddings": [query_embedding], "n_results": k}

            if where_filter:
                query_args["where"] = where_filter

            results = collection.query(**query_args)

            ids = results.get("ids", [[]])[0]
            distances = results.get("distances", [[]])[0]
            scores = [1.0 - dist for dist in distances]

            return ids, scores

        except Exception as e:
            logger.error(
                "VectorStore",
                "Error during semantic search.",
                {"error": str(e)},
                exc_info=True,
            )
            return [], []
