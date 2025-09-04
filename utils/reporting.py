# reporting.py: A utility for creating standardized report metadata.
# This helps to reduce boilerplate code in the cognitive services when they
# create `Report` objects.

from typing import Dict
from events import Task


def create_report_meta(task: Task) -> Dict:
    """
    Creates a standard dictionary of metadata for a Report based on its source Task.
    This is intended to be used with keyword argument unpacking (**kwargs) when
    instantiating a Report object, ensuring that correlation and task IDs are
    always passed correctly.

    Example:
        report = Report(status="SUCCESS", data={...}, **create_report_meta(task))
    """
    return {
        "source_task_type": task.type,
        "correlation_id": task.correlation_id,
        "source_task_id": task.task_id,
    }
