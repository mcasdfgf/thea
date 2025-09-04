# config.py

# --- Redis Configuration ---
# Settings for the Redis client, used for inter-service communication
# and background task queuing (e.g., CrystallizerService).
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB_CRYSTALLIZER = 0


# --- TCP Server Configuration ---
# Network settings for the main application server that clients connect to.
HOST = "127.0.0.1"
PORT = 8888

# --- LLM and Reranker Model Configuration ---
# Defines the endpoints and model names for the cognitive engines.
# VLLM_API_BASE is the primary endpoint for the language model.
# RERANKER_MODEL_NAME specifies the model for relevance scoring.
VLLM_HOST = "192.168.10.155"
VLLM_PORT = 8000
# VLLM_PORT = 5000 # TabbyAPI
VLLM_API_BASE = f"http://{VLLM_HOST}:{VLLM_PORT}/v1"
VLLM_TOKENIZER_URL = f"http://{VLLM_HOST}:{VLLM_PORT}/tokenize"
VLLM_MODEL_NAME = "solidrust/Hermes-3-Llama-3.1-8B-AWQ"
# VLLM_MODEL_NAME = "Llama-3.1-8B-exl2" #TabbyAPI
RERANKER_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

# --- Universal Memory Configuration ---
# Paths to persistent storage files and core memory parameters.
MEMORY_GRAPH_FILE_PATH = "memory_core.graphml"
CHRONICLE_FILE_PATH = "memory_core.chronicle.json"
CHROMA_DB_PATH = "./memory_core_chroma_db"
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
RELEVANCE_THRESHOLD = 0.55
LLM_CONTEXT_LIMIT = 8192
CONTEXT_SUMMARY_TRIGGER_PERCENTAGE = 0.65
CONVERSATION_CACHE_MAXLEN = 50

# --- System Logger Configuration ---
LOG_FILE_PATH = "system_log.txt"

# --- Cognitive Cycle and Task Configuration ---
# Parameters that control the behavior of the core cognitive loop and background tasks.
STALL_THRESHOLD = 2

DATASET_FILE_PATH = "golden_dataset.jsonl"
SPACY_MODEL_NAME = "ru_core_news_sm"

CRYSTALLIZATION_QUEUE_KEY = "crystallization_queue"

ALLOWED_NODE_TYPES_FOR_RECALL = [
    "FactNode",
    "KnowledgeCrystalNode",
    "FinalResponseNode",
    "UserImpulse",
]

# --- Memory Recall Ranking Configuration ---
# Defines the weights and thresholds for the multi-factor relevance scoring
# algorithm used by the MemoryRecallService.
RECALL_RANKING_CONFIG = {
    "weights": {
        # --- Discovery Factors ---
        "semantic_similarity_multiplier": 15,  # Boosts score based on vector similarity.
        "conceptual_intersection_bonus": 10,  # Bonus for each concept match.
        "associative_chain_bonus": 20,  # Bonus for nodes found via graph traversal from other insights.
        "cross_validation_bonus": 40,  # Major bonus if a node is found by both semantic and conceptual search.
        # --- Node Type Bonuses (DEPRECATED) ---
        # This is kept for backward compatibility but is no longer used.
        # Contextual ranking is now preferred over static type-based bonuses.
        "node_type_bonus": {},
    },
    "recall": {
        "semantic_top_k": 50,  # How many candidates to fetch from the initial vector search.
        "recall_limit": 30,  # The total number of candidates to consider after initial ranking.
        "final_top_n": 5,  # How many of the best candidates to return to the synthesis service.
    },
}
