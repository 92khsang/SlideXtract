import pytest

from slidextract.concurrency.thread_pool import TaskMultiThreador
from slidextract.concurrency.types import TaskResult


# Example processing function
def mock_processing_function(task: int) -> int:
    return task * 2


@pytest.mark.asyncio
async def test_task_multi_threador():
    tasks = iter(range(10))  # Generate tasks from 0 to 9

    results = []
    async with TaskMultiThreador(max_workers=3) as threador:
        async for result in threador.process_tasks(
                tasks, mock_processing_function, batch_size=3
        ):
            results.append(result)

    assert len(results) == 10
    for i, result in enumerate(results):
        assert isinstance(result, TaskResult)
        assert result.success is True
        assert result.result == i * 2
        assert result.exception is None


@pytest.mark.asyncio
async def test_task_multi_threador_with_exception():
    def faulty_function(task):
        if task == 5:
            raise ValueError("Test Exception")
        return task * 2

    tasks = iter(range(10))

    results = []
    async with TaskMultiThreador(max_workers=3) as threador:
        async for result in threador.process_tasks(
                tasks, faulty_function, batch_size=3
        ):
            results.append(result)

    assert len(results) == 10
    for result in results:
        assert isinstance(result, TaskResult)
        if not result.success:
            assert isinstance(result.exception, ValueError)
        else:
            assert result.result == result.task * 2
