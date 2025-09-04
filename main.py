# main.py: The entry point and core lifecycle manager for the T.H.E.A. cognitive architecture.
# This script initializes all components (Memory, Orchestrator, Services),
# sets up the TCP server for client connections, and handles graceful shutdown.

import asyncio
import signal
from typing import Optional, List

from logger import logger
from config import *
from memory.memory_core import (
    UniversalMemory,
)
from orchestrator import Orchestrator
from command_processor import CommandProcessor

from services.base import CognitiveService

from services.simple_executor_service import SimpleExecutorService
from services.synthesis_service import SynthesisService
from services.memory_recall_service import MemoryRecallService
from services.web_search_service import WebSearchService
from services.reflection_service import ReflectionService
from services.crystallizer_service import CrystallizerService
from services.fact_ingestion_service import FactIngestionService
from services.enrichment_planner_service import EnrichmentPlannerService
from services.memory_compressor_service import MemoryCompressorService


async def main():
    # --- 1. Core Components Initialization ---
    logger.info("Main", "--- Initializing T.H.E.A. Core  ---")

    memory = UniversalMemory(
        schema_path="memory/schema.yaml", snapshot_path=MEMORY_GRAPH_FILE_PATH
    )

    orchestrator = Orchestrator(memory)

    service_instances: List[CognitiveService] = [
        EnrichmentPlannerService(orchestrator, memory),
        SimpleExecutorService(orchestrator, memory),
        SynthesisService(orchestrator, memory),
        MemoryRecallService(orchestrator, memory),
        WebSearchService(orchestrator, memory),
        ReflectionService(orchestrator, memory),
        CrystallizerService(orchestrator, memory),
        FactIngestionService(orchestrator, memory),
        MemoryCompressorService(orchestrator, memory),
    ]
    for service in service_instances:
        orchestrator.register_service(service)

    # --- 2. Service Registration ---
    # Register all cognitive services with the orchestrator.
    # The orchestrator uses a routing table to delegate tasks to the appropriate service.
    command_processor = CommandProcessor(
        send_system_message_func=orchestrator.send_system_message,
        orchestrator=orchestrator,
    )

    last_impulse_id: Optional[str] = None

    # --- 3. Client Connection Handler ---
    # This function is the main loop for handling a single client connection.
    async def handle_client(reader, writer):
        nonlocal last_impulse_id
        await orchestrator.send_system_message(writer, "T.H.E.A. Core is online.")
        try:
            while not command_processor._shutdown_event.is_set():
                raw_data = await reader.read(4096)
                if not raw_data:
                    break
                user_input = raw_data.decode("utf-8").strip()
                if not user_input:
                    continue
                if command_processor.is_command(user_input):
                    await command_processor.execute(user_input, writer)
                else:
                    new_impulse_id = await orchestrator.handle_user_impulse(
                        user_input, writer
                    )
                    last_impulse_id = new_impulse_id
        except (ConnectionResetError, asyncio.IncompleteReadError):
            logger.warning("Main", "Client connection lost unexpectedly.")
        finally:
            if writer and not writer.is_closing():
                writer.close()
                await writer.wait_closed()

    # --- 4. Server Startup and Graceful Shutdown ---
    # The main application lifecycle. It starts the server, listens for shutdown signals (Ctrl+C),
    # and ensures all resources (services, memory) are closed correctly.
    server = None
    try:
        await orchestrator.start_all_services()
        server = await asyncio.start_server(handle_client, HOST, PORT)

        addr = server.sockets[0].getsockname()
        print(f"✅ T.H.E.A. Core is running. Listening on: {addr[0]}:{addr[1]}")

        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(
                sig, lambda s=sig: command_processor._shutdown_event.set()
            )

        await command_processor._shutdown_event.wait()

    except Exception as e:
        logger.error(
            "Main",
            "Critical error in main application loop.",
            {"error": str(e)},
            exc_info=True,
        )
    finally:
        # The shutdown sequence is critical for data integrity.
        # It ensures that all services are stopped before the memory state is saved to disk.
        logger.info("Main", "--- Initiating shutdown sequence ---")

        if server:
            server.close()
            await server.wait_closed()
            logger.info("Main", "TCP server stopped.")

        await orchestrator.stop_all_services()
        logger.info("Main", "All cognitive services stopped.")

        if memory and not command_processor._shutdown_flags.get(
            "memory_cleared", False
        ):
            memory.close()
            logger.info("Main", "Memory successfully saved on normal shutdown.")
        else:
            logger.info("Main", "Memory was cleared by command, no save required.")

        logger.info("Main", "--- T.H.E.A. Core has shut down gracefully ---")


# --- Application Entry Point ---
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Main", "KeyboardInterrupt received. Shutting down...")
