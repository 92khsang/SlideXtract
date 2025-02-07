from slidextract.concurrency.process_pool import TaskMultiProcessor
from slidextract.concurrency.types import TaskResult


def mock_processing_function(task: int) -> int:
    return task * 2


def faulty_function(task):
    if task == 5:
        raise ValueError("Test Exception")
    return task * 2


def test_task_multi_processor():
    """Test TaskMultiProcessor with a normal processing function."""
    tasks = iter(range(10))

    with TaskMultiProcessor(max_workers=3) as processor:
        results = list(
            processor.process_tasks(tasks, mock_processing_function, batch_size=3)
        )

    assert len(results) == 10
    for i, result in enumerate(results):
        assert isinstance(result, TaskResult)
        assert result.success is True
        assert result.result == i * 2
        assert result.exception is None


def test_task_multi_processor_with_exception():
    """Test TaskMultiProcessor handling exceptions in tasks."""

    tasks = iter(range(10))

    with TaskMultiProcessor(max_workers=3) as processor:
        results = list(processor.process_tasks(tasks, faulty_function, batch_size=3))

    assert len(results) == 10
    for result in results:
        assert isinstance(result, TaskResult)
        if not result.success:
            assert isinstance(result.exception, ValueError)
        else:
            assert result.result == result.task * 2
