"""Unit tests for CompleteWorkTool with output_schema feature."""

import pytest
from pydantic import BaseModel
from webtask._internal.agent.tools import CompleteWorkTool
from webtask._internal.agent.run import TaskResult, TaskStatus

pytestmark = pytest.mark.unit


class SearchResult(BaseModel):
    """Example output schema for testing."""

    title: str
    url: str
    snippet: str


class TestCompleteWorkToolWithOutputSchema:
    """Test CompleteWorkTool with optional output_schema."""

    @pytest.mark.unit
    def test_complete_work_with_schema(self):
        """Test complete_work with output_schema (happy path)."""
        result = TaskResult()
        tool = CompleteWorkTool(result, output_schema=SearchResult)

        # With schema, output must match SearchResult
        search_data = {
            "title": "Pydantic Documentation",
            "url": "https://docs.pydantic.dev",
            "snippet": "Data validation using Python type hints",
        }

        params = tool.Params(feedback="Extracted search result", output=search_data)

        import asyncio

        asyncio.run(tool.execute(params))

        assert result.status == TaskStatus.COMPLETED
        assert result.feedback == "Extracted search result"

        # Output is validated and converted to SearchResult instance by Pydantic
        assert isinstance(result.output, SearchResult)
        assert result.output.title == "Pydantic Documentation"
        assert result.output.url == "https://docs.pydantic.dev"
        assert result.output.snippet == "Data validation using Python type hints"
