from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import AsyncIterator, Callable, Iterator, TypeVar

from slidextract.concurrency.types import TaskResult

TASK = TypeVar("TASK")
RESULT = TypeVar("RESULT")


class TaskMultiThreador:
    """
    Handles the processing of generic tasks using a ThreadPoolExecutor.
    Supports processing tasks from an iterator.
    """

    def __init__(self, max_workers: int = 10):
        self.executor = ThreadPoolExecutor(max_workers)

    async def process_tasks(
            self,
            tasks: Iterator[TASK],
            process_task: Callable[[TASK], RESULT],
            batch_size: int = 10,
    ) -> AsyncIterator[TaskResult[TASK, RESULT]]:
        """
        Processes tasks concurrently in batches from an iterator.

        Args:
            tasks (Iterator[TASK]): An iterator of tasks to process.
            process_task (Callable[[TASK], RESULT]): A function to process each task.
            batch_size (int): The number of tasks to process in each batch.

        Yields:
            TaskResult[TASK, RESULT]: A TaskResult object for each processed task.
        """
        loop = asyncio.get_running_loop()

        async def process_single_task(task: TASK) -> TaskResult[TASK, RESULT]:
            try:
                result_ = await loop.run_in_executor(self.executor, process_task, task)
                return TaskResult(task=task, result=result_)
            except Exception as e:
                return TaskResult(task=task, success=False, exception=e)

        while batch := [task for _, task in zip(range(batch_size), tasks)]:
            results = await asyncio.gather(
                *[process_single_task(task) for task in batch]
            )
            for result in results:
                yield result

    async def __aenter__(self) -> TaskMultiThreador:
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        self.executor.shutdown()
