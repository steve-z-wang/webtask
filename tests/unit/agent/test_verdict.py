"""Tests for Verdict class."""

import pytest
from webtask.agent import Verdict


@pytest.mark.unit
def test_verdict_bool_conversion():
    """Test that Verdict can be used in boolean context."""
    passed_verdict = Verdict(passed=True, feedback="Condition met")
    failed_verdict = Verdict(passed=False, feedback="Condition not met")

    assert bool(passed_verdict) is True
    assert bool(failed_verdict) is False

    # Can use in if statements
    if passed_verdict:
        result = "passed"
    else:
        result = "failed"
    assert result == "passed"


@pytest.mark.unit
def test_verdict_equality_with_boolean():
    """Test that Verdict can be compared with boolean."""
    passed_verdict = Verdict(passed=True, feedback="Condition met")
    failed_verdict = Verdict(passed=False, feedback="Condition not met")

    assert (passed_verdict == True) is True  # noqa: E712
    assert (passed_verdict != False) is True  # noqa: E712
    assert (failed_verdict == False) is True  # noqa: E712
    assert (failed_verdict != True) is True  # noqa: E712


@pytest.mark.unit
def test_verdict_attributes():
    """Test Verdict attributes."""
    verdict = Verdict(passed=True, feedback="Cart has 7 items")

    assert verdict.passed is True
    assert verdict.feedback == "Cart has 7 items"


@pytest.mark.unit
def test_verdict_string_representation():
    """Test Verdict string representation."""
    verdict = Verdict(passed=True, feedback="Test passed")
    assert "passed=True" in str(verdict)
    assert "Test passed" in str(verdict)
