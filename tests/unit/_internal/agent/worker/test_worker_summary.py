"""Unit tests for Worker summary generation with reasoning."""

import pytest
from webtask._internal.agent.worker.worker import Worker, ToolCallPair
from webtask.llm import AssistantMessage, ToolResultMessage, TextContent

pytestmark = pytest.mark.unit


class TestWorkerSummary:
    """Test Worker._build_summary() generates correct format with reasoning."""

    @pytest.fixture
    def worker(self, mocker):
        """Create a Worker instance with mocked dependencies."""
        mock_llm = mocker.Mock()
        mock_session_browser = mocker.Mock()
        return Worker(
            llm=mock_llm,
            session_browser=mock_session_browser,
            wait_after_action=0.1,
        )

    def test_build_summary_with_reasoning_and_actions(self, worker):
        """Test summary includes reasoning and actions in correct format."""
        pairs = [
            ToolCallPair(
                assistant_msg=AssistantMessage(
                    content=[TextContent(text="I need to navigate first")],
                    tool_calls=[],
                ),
                tool_result_msg=ToolResultMessage(results=[], content=[]),
                descriptions=["Navigated to https://example.com"],
                reasoning="I need to navigate first",
            ),
            ToolCallPair(
                assistant_msg=AssistantMessage(content=[], tool_calls=[]),
                tool_result_msg=ToolResultMessage(results=[], content=[]),
                descriptions=["Clicked button-5", "Filled input-1 with 'test'"],
                reasoning="Now I'll interact with the page",
            ),
        ]

        summary = worker._build_summary(pairs)

        # Verify format
        assert "Step 1:" in summary
        assert "Step 2:" in summary
        assert "Reasoning:" in summary
        assert "Actions:" in summary
        assert "I need to navigate first" in summary
        assert "Now I'll interact with the page" in summary
        assert "- Navigated to https://example.com" in summary
        assert "- Clicked button-5" in summary
        assert "- Filled input-1 with 'test'" in summary

    def test_build_summary_with_multiline_reasoning(self, worker):
        """Test summary handles multiline reasoning correctly."""
        pairs = [
            ToolCallPair(
                assistant_msg=AssistantMessage(content=[], tool_calls=[]),
                tool_result_msg=ToolResultMessage(results=[], content=[]),
                descriptions=["Clicked button-1"],
                reasoning="First line of reasoning\nSecond line of reasoning\nThird line",
            ),
        ]

        summary = worker._build_summary(pairs)

        # Verify multiline reasoning is properly indented
        assert "Reasoning:" in summary
        assert "    First line of reasoning" in summary
        assert "    Second line of reasoning" in summary
        assert "    Third line" in summary

    def test_build_summary_without_reasoning(self, worker):
        """Test summary works when reasoning is None."""
        pairs = [
            ToolCallPair(
                assistant_msg=AssistantMessage(content=[], tool_calls=[]),
                tool_result_msg=ToolResultMessage(results=[], content=[]),
                descriptions=["Waited 1.0 seconds"],
                reasoning=None,
            ),
        ]

        summary = worker._build_summary(pairs)

        # Should still have step and actions, but no reasoning section
        assert "Step 1:" in summary
        assert "Reasoning:" not in summary
        assert "Actions:" in summary
        assert "- Waited 1.0 seconds" in summary

    def test_build_summary_empty_pairs(self, worker):
        """Test summary returns empty string for no pairs."""
        summary = worker._build_summary([])
        assert summary == ""

    def test_build_summary_multiple_steps(self, worker):
        """Test summary correctly numbers multiple steps."""
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

        summary = worker._build_summary(pairs)

        # Verify all steps are numbered correctly
        assert "Step 1:" in summary
        assert "Step 2:" in summary
        assert "Step 3:" in summary
        assert summary.count("Reasoning:") == 3
        assert summary.count("Actions:") == 3

    def test_build_summary_with_no_actions(self, worker):
        """Test summary when step has reasoning but no actions."""
        pairs = [
            ToolCallPair(
                assistant_msg=AssistantMessage(content=[], tool_calls=[]),
                tool_result_msg=ToolResultMessage(results=[], content=[]),
                descriptions=[],
                reasoning="Thinking but no actions taken",
            ),
        ]

        summary = worker._build_summary(pairs)

        # Should have reasoning but no actions section
        assert "Step 1:" in summary
        assert "Reasoning:" in summary
        assert "Thinking but no actions taken" in summary
        assert "Actions:" not in summary

    def test_summary_format_matches_specification(self, worker):
        """Test that the summary format exactly matches the specified format."""
        pairs = [
            ToolCallPair(
                assistant_msg=AssistantMessage(content=[], tool_calls=[]),
                tool_result_msg=ToolResultMessage(results=[], content=[]),
                descriptions=["Navigated to https://example.com/login"],
                reasoning="I need to navigate to the login page first before I can enter credentials.",
            ),
            ToolCallPair(
                assistant_msg=AssistantMessage(content=[], tool_calls=[]),
                tool_result_msg=ToolResultMessage(results=[], content=[]),
                descriptions=["Filled input-1 with 'testuser'"],
                reasoning="The login page has loaded successfully. I can see two input fields (input-1 and input-2) and a submit button (button-5). I'll fill in the username field first with 'testuser'.",
            ),
        ]

        summary = worker._build_summary(pairs)

        expected_lines = [
            "",
            "Step 1:",
            "  Reasoning:",
            "    I need to navigate to the login page first before I can enter credentials.",
            "  Actions:",
            "    - Navigated to https://example.com/login",
            "",
            "Step 2:",
            "  Reasoning:",
            "    The login page has loaded successfully. I can see two input fields (input-1 and input-2) and a submit button (button-5). I'll fill in the username field first with 'testuser'.",
            "  Actions:",
            "    - Filled input-1 with 'testuser'",
        ]

        assert summary == "\n".join(expected_lines)
