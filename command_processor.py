# command_processor.py: Handles special user inputs prefixed with '!'.
# These commands provide a direct way to interact with the system's core
# functionalities, such as saving memory, clearing data, or triggering
# specific cognitive processes manually.

import os
import shutil
import asyncio
from typing import Callable, Coroutine
import json

from logger import logger
from config import MEMORY_GRAPH_FILE_PATH, CHROMA_DB_PATH
from events import Task
from memory.memory_core import UniversalMemory
from dataclasses import asdict


class CommandProcessor:
    def __init__(
        self,
        send_system_message_func: Callable[[asyncio.StreamWriter, str], Coroutine],
        orchestrator,
    ):
        self._send_system_message = send_system_message_func
        self._orchestrator = orchestrator
        self._memory = orchestrator._memory
        self._shutdown_event = asyncio.Event()
        self._shutdown_flags = {}

    def is_command(self, user_input: str) -> bool:
        return user_input.strip().startswith("!")

    async def execute(self, command: str, writer: asyncio.StreamWriter):
        command_parts = command.strip().split(" ")
        command_name = command_parts[0]
        args = command_parts[1:]

        if command_name == "!save":
            # Command: !save
            # Manually triggers the saving of the current memory state to disk.
            # self._memory.save_snapshot()
            self._memory.close()
            await self._send_system_message(writer, "Memory state has been saved.")

        elif command_name == "!clear_memory":
            # Command: !clear_memory
            # A destructive operation that completely wipes the persistent memory.
            # This involves deleting the graph, chronicle, and vector store files.
            # It then triggers a graceful shutdown of the core for a clean restart.
            self._memory.close()

            if os.path.exists(MEMORY_GRAPH_FILE_PATH):
                os.remove(MEMORY_GRAPH_FILE_PATH)
                logger.info(
                    "CommandProcessor", f"Graph file deleted: {MEMORY_GRAPH_FILE_PATH}"
                )

            chronicle_path = self._memory.time_store.chronicle_path
            if os.path.exists(chronicle_path):
                os.remove(chronicle_path)
                logger.info(
                    "CommandProcessor", f"Chronicle file deleted: {chronicle_path}"
                )

            if os.path.isdir(CHROMA_DB_PATH):
                shutil.rmtree(CHROMA_DB_PATH)
                logger.info(
                    "CommandProcessor", f"ChromaDB directory deleted: {CHROMA_DB_PATH}"
                )

            self._shutdown_flags["memory_cleared"] = True

            await self._send_system_message(
                writer, "Memory has been completely cleared. The core will now restart."
            )

            await asyncio.sleep(0.1)

            self._shutdown_event.set()
            return

        elif command_name == "!reflect":
            # Command: !reflect
            # Manually triggers the deep reflection process, which analyzes the entire
            # memory to synthesize new insights and strengthen existing knowledge.
            task = Task(type="run_deep_reflection", payload={})
            future = self._orchestrator.execute_single_task(task)

            async def await_and_report():
                report = await future
                report_data_str = json.dumps(
                    asdict(report), ensure_ascii=False, indent=2
                )
                await self._send_system_message(
                    writer, f"[REFLECTION REPORT]:\n{report_data_str}"
                )

            asyncio.create_task(await_and_report())
            await self._send_system_message(
                writer, "Deep reflection process has been started in the background."
            )

        elif command_name == "!fact":
            # Command: !fact <text>
            # Directly injects a piece of information as a verified fact into memory.
            # This bypasses the usual cognitive cycle and is useful for bootstrapping
            # the system's knowledge base or for testing.
            fact_text = " ".join(args)
            if not fact_text:
                await self._send_system_message(
                    writer,
                    "Error: The !fact command must be followed by the fact text.",
                )
                return

            logger.info(
                "CommandProcessor",
                f"Initiating task to ingest fact: '{fact_text}'",
            )
            fact_task = Task(type="ingest_fact", payload={"fact_text": fact_text})

            report = await self._orchestrator.execute_single_task(fact_task)

            if (
                report.status == "SUCCESS"
                and report.data.get("status") == "Acknowledge"
            ):
                ack_task = Task(
                    type="synthesize_acknowledgement",
                    payload={"hint": report.data.get("hint")},
                )
                ack_report = await self._orchestrator.execute_single_task(ack_task)
                ack_text = ack_report.data.get("text", "Fact acknowledged.")
                await self._send_system_message(writer, ack_text)
            else:
                await self._send_system_message(
                    writer, "An error occurred while processing the fact."
                )
        else:
            await self._send_system_message(writer, f"Unknown command: {command_name}")
