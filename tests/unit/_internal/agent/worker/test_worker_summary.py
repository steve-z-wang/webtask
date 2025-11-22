"""Unit tests for TaskRunner summary generation with reasoning."""

import pytest
from webtask._internal.agent.task_runner import TaskRunner, ToolCallPair
from webtask._internal.agent.run import Run, TaskResult, TaskStatus
from webtask.llm import AssistantMessage, ToolResultMessage, TextContent

pytestmark = pytest.mark.unit


class TestTaskRunnerSummary:
    """Test TaskRunner._build_summary() generates correct format with reasoning."""

    @pytest.fixture
    def task_runner(self, mocker):
        """Create a TaskRunner instance with mocked dependencies."""
        mock_llm = mocker.Mock()
        mock_browser = mocker.Mock()
        return TaskRunner(
            llm=mock_llm,
            browser=mock_browser,
        )

    @pytest.mark.unit
    def test_build_summary_with_reasoning_and_actions(self, task_runner):
        """Test summary includes reasoning and actions in correct format."""
        pairs = [
            ToolCallPair(
                assistant_msg=AssistantMessage(
                    content=[TextContent(text="I need to navigate first")],
                    tool_calls=[],
                ),
                tool_result_msg=ToolResultMessage(results=[], content=[]),
                descriptions=["Went to https://example.com"],
                reasoning="I need to go to the page first",
            ),
            ToolCallPair(
                assistant_msg=AssistantMessage(content=[], tool_calls=[]),
                tool_result_msg=ToolResultMessage(results=[], content=[]),
                descriptions=["Clicked button-5", "Filled input-1 with 'test'"],
                reasoning="Now I'll interact with the page",
            ),
        ]

        summary = task_runner._build_summary(pairs)

        # Verify format (reasoning as main bullet, actions indented)
        assert "- I need to go to the page first" in summary
        assert "- Now I'll interact with the page" in summary
        assert "  - Went to https://example.com" in summary
        assert "  - Clicked button-5" in summary
        assert "  - Filled input-1 with 'test'" in summary

    @pytest.mark.unit
    def test_build_summary_with_multiline_reasoning(self, task_runner):
        """Test summary handles multiline reasoning correctly."""
        pairs = [
            ToolCallPair(
                assistant_msg=AssistantMessage(content=[], tool_calls=[]),
                tool_result_msg=ToolResultMessage(results=[], content=[]),
                descriptions=["Clicked button-1"],
                reasoning="First line of reasoning\nSecond line of reasoning\nThird line",
            ),
        ]

        summary = task_runner._build_summary(pairs)

        # Verify multiline reasoning is properly formatted
        assert "- First line of reasoning" in summary
        assert "  Second line of reasoning" in summary
        assert "  Third line" in summary
        assert "  - Clicked button-1" in summary

    @pytest.mark.unit
    def test_build_summary_without_reasoning(self, task_runner):
        """Test summary works when reasoning is None."""
        pairs = [
            ToolCallPair(
                assistant_msg=AssistantMessage(content=[], tool_calls=[]),
                tool_result_msg=ToolResultMessage(results=[], content=[]),
                descriptions=["Waited 1.0 seconds"],
                reasoning=None,
            ),
        ]

        summary = task_runner._build_summary(pairs)

        # Should have actions but no reasoning
        assert "  - Waited 1.0 seconds" in summary

    @pytest.mark.unit
    def test_build_summary_empty_pairs(self, task_runner):
        """Test summary returns empty string for no pairs."""
        summary = task_runner._build_summary([])
        assert summary == ""

    @pytest.mark.unit
    def test_build_summary_multiple_steps(self, task_runner):
        """Test summary handles multiple pairs correctly."""
        pairs = [
            ToolCallPair(
                assistant_msg=AssistantMessage(content=[], tool_calls=[]),
                tool_result_msg=ToolResultMessage(results=[], content=[]),
                descriptions=["Action 1"],
                reasoning="Step 1 reasoning",
            ),
            ToolCallPair(
                assistant_msg=AssistantMessage(content=[], tool_calls=[]),
                tool_result_msg=ToolResultMessage(results=[], content=[]),
                descriptions=["Action 2"],
                reasoning="Step 2 reasoning",
            ),
            ToolCallPair(
                assistant_msg=AssistantMessage(content=[], tool_calls=[]),
                tool_result_msg=ToolResultMessage(results=[], content=[]),
                descriptions=["Action 3"],
                reasoning="Step 3 reasoning",
            ),
        ]

        summary = task_runner._build_summary(pairs)

        # Verify all pairs are included
        assert "- Step 1 reasoning" in summary
        assert "- Step 2 reasoning" in summary
        assert "- Step 3 reasoning" in summary
        assert "  - Action 1" in summary
        assert "  - Action 2" in summary
        assert "  - Action 3" in summary

    @pytest.mark.unit
    def test_build_summary_with_no_actions(self, task_runner):
        """Test summary when step has reasoning but no actions."""
        pairs = [
            ToolCallPair(
                assistant_msg=AssistantMessage(content=[], tool_calls=[]),
                tool_result_msg=ToolResultMessage(results=[], content=[]),
                descriptions=[],
                reasoning="Thinking but no actions taken",
            ),
        ]

        summary = task_runner._build_summary(pairs)

        # Should have reasoning only (no actions)
        assert "- Thinking but no actions taken" in summary

    @pytest.mark.unit
    def test_summary_format_matches_specification(self, task_runner):
        """Test that the summary format exactly matches the implemented format."""
        pairs = [
            ToolCallPair(
                assistant_msg=AssistantMessage(content=[], tool_calls=[]),
                tool_result_msg=ToolResultMessage(results=[], content=[]),
                descriptions=["Went to https://example.com/login"],
                reasoning="I need to go to the login page first before I can enter credentials.",
            ),
            ToolCallPair(
                assistant_msg=AssistantMessage(content=[], tool_calls=[]),
                tool_result_msg=ToolResultMessage(results=[], content=[]),
                descriptions=["Filled input-1 with 'testuser'"],
                reasoning="The login page has loaded successfully. I can see two input fields (input-1 and input-2) and a submit button (button-5). I'll fill in the username field first with 'testuser'.",
            ),
        ]

        summary = task_runner._build_summary(pairs)

        expected_lines = [
            "- I need to go to the login page first before I can enter credentials.",
            "  - Went to https://example.com/login",
            "- The login page has loaded successfully. I can see two input fields (input-1 and input-2) and a submit button (button-5). I'll fill in the username field first with 'testuser'.",
            "  - Filled input-1 with 'testuser'",
        ]

        assert summary == "\n".join(expected_lines)


class TestTaskRunnerPreviousRuns:
    """Test TaskRunner._format_previous_runs() generates correct format."""

    @pytest.fixture
    def task_runner(self, mocker):
        """Create a TaskRunner instance with mocked dependencies."""
        mock_llm = mocker.Mock()
        mock_browser = mocker.Mock()
        return TaskRunner(
            llm=mock_llm,
            browser=mock_browser,
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
                summary="- Navigated to google.com\n  - Loaded homepage\n- Searched for python\n  - Entered text\n  - Clicked search",
                messages=[],
                steps_used=3,
                max_steps=10,
            ),
            Run(
                task_description="Click on the first result",
                result=TaskResult(
                    status=TaskStatus.ABORTED, feedback="Element not found"
                ),
                summary="- Attempted to click first result\n  - Could not locate element",
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

        # Verify it does NOT contain the detailed summary
        assert "Navigated to google.com" not in formatted
        assert "Entered text" not in formatted
        assert "Could not locate element" not in formatted
