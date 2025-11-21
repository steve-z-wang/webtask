"""Tests for Verdict class."""

from webtask.agent import Verdict, Status


def test_verdict_bool_conversion():
    """Test that Verdict can be used in boolean context."""
    passed_verdict = Verdict(passed=True, feedback="Condition met", status=Status.COMPLETED)
    failed_verdict = Verdict(passed=False, feedback="Condition not met", status=Status.ABORTED)

    assert bool(passed_verdict) is True
    assert bool(failed_verdict) is False

    # Can use in if statements
    if passed_verdict:
        result = "passed"
    else:
        result = "failed"
    assert result == "passed"


def test_verdict_equality_with_boolean():
    """Test that Verdict can be compared with boolean."""
    passed_verdict = Verdict(passed=True, feedback="Condition met", status=Status.COMPLETED)
    failed_verdict = Verdict(passed=False, feedback="Condition not met", status=Status.ABORTED)

    assert passed_verdict == True
    assert passed_verdict != False
    assert failed_verdict == False
    assert failed_verdict != True


def test_verdict_attributes():
    """Test Verdict attributes."""
    verdict = Verdict(
        passed=True,
        feedback="Cart has 7 items",
        status=Status.COMPLETED
    )

    assert verdict.passed is True
    assert verdict.feedback == "Cart has 7 items"
    assert verdict.status == Status.COMPLETED


def test_verdict_string_representation():
    """Test Verdict string representation."""
    verdict = Verdict(passed=True, feedback="Test passed", status=Status.COMPLETED)
    assert "passed=True" in str(verdict)
    assert "Test passed" in str(verdict)
