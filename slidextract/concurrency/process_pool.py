from __future__ import annotations

from multiprocessing import Pool
from typing import Iterator, Callable, TypeVar

from slidextract.concurrency.types import TaskResult

TASK = TypeVar("TASK")
RESULT = TypeVar("RESULT")


class TaskMultiProcessor:
    """
    Handles the processing of generic tasks using multiprocessing.Pool.
    Supports processing tasks from an iterator.
    """

    def __init__(self, max_workers: int = 5):
        self.max_workers = max_workers
        self.pool = None

    def process_tasks(
            self,
            tasks: Iterator[TASK],
            process_task: Callable[[TASK], RESULT],
            batch_size: int = 5,
    ) -> Iterator[TaskResult[TASK, RESULT]]:
        """
        Processes tasks in parallel using multiprocessing.

        Args:
            tasks (Iterator[TASK]): An iterator of tasks to process.
            process_task (Callable[[TASK], RESULT]): A function to process each task.
            batch_size (int): The number of tasks to process in each batch.

        Yields:
            TaskResult[TASK, RESULT]: A TaskResult object for each processed task.
        """
        if self.pool is None:
            self.pool = Pool(processes=self.max_workers)

        try:
            while batch := [task for _, task in zip(range(batch_size), tasks)]:
                async_results = [
                    self.pool.apply_async(process_task, (task,)) for task in batch
                ]

                for task, async_result in zip(batch, async_results):
                    try:
                        result = async_result.get()
                        yield TaskResult(task=task, result=result)
                    except Exception as e:
                        yield TaskResult(task=task, success=False, exception=e)
        finally:
            self.cleanup()

    def cleanup(self):
        if self.pool is not None:
            self.pool.close()
            self.pool.join()
            self.pool = None

    def __enter__(self) -> "TaskMultiProcessor":
        self.pool = Pool(processes=self.max_workers)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.cleanup()
