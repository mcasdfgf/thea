# file: nexus_vision/backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from contextlib import asynccontextmanager

# --- Core Application Imports ---
# `settings` provides configuration values from the .env_vision file.
from app.core.config import settings

# `periodic_graph_reload` is the background task that watches for changes in the graph file.
from app.core.graph_loader import periodic_graph_reload

# `graph_endpoints` contains all API routes related to the graph.
from app.api.endpoints import graph as graph_endpoints


# A lifespan context manager is a modern FastAPI feature for handling startup and shutdown events.
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the application's lifespan events.
    On startup, it launches the background task to monitor the graph file.
    On shutdown, it gracefully cancels the task.
    """
    print("Starting background graph reload task...")
    # Create and start the background task.
    task = asyncio.create_task(periodic_graph_reload())

    # The 'yield' statement passes control back to the application, which runs until shutdown.
    yield

    # --- Shutdown logic ---
    print("Stopping background task...")
    task.cancel()
    try:
        # Wait for the task to acknowledge cancellation.
        await task
    except asyncio.CancelledError:
        print("Background task stopped successfully.")


# Initialize the main FastAPI application instance.
app = FastAPI(
    title="Nexus Vision API",
    description="API for the T.H.E.A. memory graph visualizer.",
    version="1.0.0",
    # Link the lifespan manager to the application.
    lifespan=lifespan,
)

# --- CORS (Cross-Origin Resource Sharing) Configuration ---
# This is a security feature that controls which frontend domains are allowed to
# make requests to this API.
origins = [
    settings.FRONTEND_ORIGIN,
    "http://localhost:5173",  # Standard Vite dev server port
    "http://localhost:3000",  # Standard Create React App dev server port
]

# Log the applied CORS settings for easier debugging during setup.
print("--- CORS Configuration ---")
print(f"Allowing origins: {origins}")
print("--------------------------")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all request headers
)

# --- API Router Inclusion ---
# This line attaches all the routes defined in `app/api/endpoints/graph.py`
# to the main application, under the `/api` prefix.
app.include_router(graph_endpoints.router, prefix="/api", tags=["Graph"])


# --- Root Endpoint ---
@app.get("/")
def read_root():
    """A simple root endpoint to confirm that the API is running."""
    return {"message": "Welcome to the Nexus Vision API"}
