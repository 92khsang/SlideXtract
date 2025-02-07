from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Optional, TypeVar

TASK = TypeVar("TASK")
RESULT = TypeVar("RESULT")


@dataclass
class TaskResult(Generic[TASK, RESULT]):
    """
    Holds the result of processing a single task.

    Attributes:
        task (TASK): The task that was processed.
        result (Optional[RESULT]): The result of processing the task, if any.
        success (bool): Whether the task was processed successfully.
        exception (Optional[Exception]): The exception that occurred while processing the task, if any.
    """

    task: TASK
    result: Optional[RESULT] = None
    success: bool = True
    exception: Optional[Exception] = None
