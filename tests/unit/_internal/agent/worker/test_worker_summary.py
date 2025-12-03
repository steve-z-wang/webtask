"""Unit tests for TaskRunner previous runs formatting."""

import pytest
from webtask._internal.agent.task_runner import TaskRunner
from webtask._internal.agent.run import Run, TaskResult, TaskStatus

pytestmark = pytest.mark.unit


class TestTaskRunnerPreviousRuns:
    """Test TaskRunner._format_previous_runs() generates correct format."""

    @pytest.fixture
    def task_runner(self, mocker):
        """Create a TaskRunner instance with mocked dependencies."""
        mock_llm = mocker.Mock()
        mock_tools = []
        mock_get_context = mocker.AsyncMock(return_value=[])
        return TaskRunner(
            llm=mock_llm,
            tools=mock_tools,
            get_context=mock_get_context,
        )

    @pytest.mark.unit
    def test_format_previous_runs(self, task_runner):
        """Test that previous runs are formatted with task, status, and feedback only."""
        runs = [
            Run(
                task_description="Navigate to google.com and search for 'python'",
                result=TaskResult(
                    status=TaskStatus.COMPLETED,
                    feedback="Search completed successfully",
                ),
                messages=[],
                steps_used=3,
                max_steps=10,
            ),
            Run(
                task_description="Click on the first result",
                result=TaskResult(
                    status=TaskStatus.ABORTED, feedback="Element not found"
                ),
                messages=[],
                steps_used=1,
                max_steps=10,
            ),
        ]

        formatted = task_runner._format_previous_runs(runs)

        # Verify it contains task descriptions
        assert "Navigate to google.com and search for 'python'" in formatted
        assert "Click on the first result" in formatted

        # Verify it contains status
        assert "Status: Completed" in formatted
        assert "Status: Aborted" in formatted

        # Verify it contains feedback
        assert "Feedback: Search completed successfully" in formatted
        assert "Feedback: Element not found" in formatted
