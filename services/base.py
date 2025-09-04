# base.py: Defines the abstract base class for all cognitive services.
# It provides a common interface and lifecycle management (start, stop, push_task)
# for asynchronous, queue-based workers. Each concrete service must implement
# `get_supported_tasks` and `handle_task`.

from abc import ABC, abstractmethod
from typing import Set, TYPE_CHECKING, Optional
import asyncio

from events import Task, Report
from logger import logger

if TYPE_CHECKING:
    from orchestrator import Orchestrator
    from memory_core import UniversalMemory


class CognitiveService(ABC):
    """
    An abstract base class for a background worker that processes tasks from a queue.
    """

    def __init__(
        self, service_name: str, orchestrator: "Orchestrator", memory: "UniversalMemory"
    ):
        self.service_name = service_name
        self._orchestrator = orchestrator
        self._memory = memory
        self._task_queue = asyncio.Queue()
        self._is_running = False
        self._worker_task: Optional[asyncio.Task] = None
        logger.info(f"CognitiveService:{self.service_name}", "Service initialized.")

    @abstractmethod
    def get_supported_tasks(self) -> Set[str]:
        """
        Returns a set of task type strings that this service can handle.
        This is used by the Orchestrator to build its task routing table.
        """
        pass

    async def start(self):
        if not self._is_running:
            self._is_running = True
            self._worker_task = asyncio.create_task(self._worker())
            logger.info(f"CognitiveService:{self.service_name}", "Service started.")

    async def stop(self):
        if self._is_running:
            self._is_running = False
            if self._worker_task:
                try:
                    self._worker_task.cancel()
                    await self._worker_task
                except asyncio.CancelledError:
                    pass
            logger.info(f"CognitiveService:{self.service_name}", "Service stopped.")

    async def push_task(self, task: Task):
        await self._task_queue.put(task)

    async def _worker(self):
        while self._is_running:
            try:
                task = await self._task_queue.get()
                logger.info(
                    f"CognitiveService:{self.service_name}",
                    "New task received.",
                    {"task_id": task.task_id, "type": task.type},
                )

                asyncio.create_task(self._process_task_wrapper(task))

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    f"CognitiveService:{self.service_name}",
                    "Critical error in worker loop.",
                    {"error": str(e)},
                    exc_info=True,
                )

    async def _process_task_wrapper(self, task: Task):
        # This wrapper ensures that every task execution is safely handled.
        # It catches any exceptions within the service's `handle_task` method
        # and guarantees that a report (either success or failure) is always
        # sent back to the orchestrator.
        report = None
        try:
            report = await self.handle_task(task)

            if report is None:
                # This is a critical logic error in the specific service implementation.
                # A service should ALWAYS return a Report object.
                logger.error(
                    f"CognitiveService:{self.service_name}",
                    f"Service returned None instead of a Report for task {task.task_id}. This is a critical implementation error.",
                )
                report = Report(
                    status="FAILURE",
                    source_task_type=task.type,
                    data={
                        "error": "Service returned None",
                        "details": "The service failed to produce a report object after handling the task.",
                    },
                    correlation_id=task.correlation_id,
                    source_task_id=task.task_id,
                )

            await self._orchestrator.receive_report(report)

        except Exception as e:
            logger.error(
                f"CognitiveService:{self.service_name}",
                f"Error processing task {task.task_id}",
                {"error": str(e)},
                exc_info=True,
            )

            error_report = Report(
                status="FAILURE",
                source_task_type=task.type,
                data={
                    "error": str(e),
                    "details": "The service failed to process the task due to an unhandled exception.",
                },
                correlation_id=task.correlation_id,
                source_task_id=task.task_id,
            )
            await self._orchestrator.receive_report(error_report)

    @abstractmethod
    async def handle_task(self, task: Task) -> Report:
        """
        The core logic of the service. This method is implemented by each
        concrete service to handle its specific task types.

        Args:
        task: The Task object to be processed.

        Returns:
        A Report object containing the result of the task.
        """
        pass
