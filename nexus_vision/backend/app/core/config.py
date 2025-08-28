# file: nexus_vision/backend/app/core/config.py

import os
from dotenv import load_dotenv
from pathlib import Path

# --- Dynamic Path Resolution ---
# This logic ensures that the application can find project files (like .env_vision and the graphml)
# regardless of where the script is executed from.

# 1. Determine the absolute path to the project's root directory.
# `Path(__file__)` is the path to this config.py file.
# We traverse up the directory tree to find the project root.
# This makes the configuration robust and portable.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent

# 2. Construct the full path to the environment file.
env_path = PROJECT_ROOT / "nexus_vision" / ".env_vision"
# Load the environment variables from the specified .env file.
load_dotenv(dotenv_path=env_path)


class Settings:
    """
    A centralized class for application settings.
    It reads values from environment variables, providing default fallbacks.
    """

    # 3. Construct the absolute path to the graph file.
    # We get the relative path from the environment variable...
    relative_path_from_env = os.getenv("GRAPH_FILE_PATH", "memory_core.graphml")
    # ...and join it with the project root to get a guaranteed absolute path.
    GRAPH_FILE_PATH: str = str(PROJECT_ROOT / relative_path_from_env)

    # --- API and CORS Settings ---
    BACKEND_HOST: str = os.getenv("BACKEND_HOST", "127.0.0.1")
    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", 8008))
    FRONTEND_ORIGIN: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")


# Create a singleton instance of the settings to be imported by other modules.
settings = Settings()

# --- Startup Sanity Check ---
# This block prints key configuration details on startup, which is invaluable for debugging setup issues.
print("--- Nexus Vision Configuration ---")
print(f"Project Root Detected: {PROJECT_ROOT}")
print(f"Attempting to load .env from: {env_path}")
print(f"Graph File Path from .env: {os.getenv('GRAPH_FILE_PATH')}")
print(f"Final Absolute Graph File Path: {settings.GRAPH_FILE_PATH}")
print(f"Checking if graph file exists... -> {os.path.exists(settings.GRAPH_FILE_PATH)}")
print("---------------------------------")
