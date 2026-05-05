"""Tests for MAEPSession state machine (budget_cents version)."""

import pytest
from agent_sdk.protocol import MAEPSession, TaskSpec, TaskResult, Stage


def test_initial_stage():
    session = MAEPSession(task_id="test-1")
    assert session.stage == Stage.REGISTERED


def test_full_happy_path():
    session = MAEPSession(task_id="test-1")
    spec = TaskSpec(task_type="test", description="hello", budget_cents=100)
    session.delegate(spec)
    assert session.stage == Stage.DELEGATED

    result = TaskResult.from_data("world")
    session.execute(result)
    assert session.stage == Stage.EXECUTED

    session.settle(True)
    assert session.stage == Stage.SETTLED


def test_cannot_skip_stages():
    session = MAEPSession(task_id="test-1")

    with pytest.raises(ValueError):
        session.execute(TaskResult.from_data("x"))

    with pytest.raises(ValueError):
        session.settle(True)


def test_settle_rejected_goes_to_dispute():
    session = MAEPSession(task_id="test-1")
    session.delegate(TaskSpec(task_type="t", description="d", budget_cents=100))
    session.execute(TaskResult.from_data("result"))
    session.settle(False)
    assert session.stage == Stage.DISPUTED


def test_result_hash():
    result = TaskResult.from_data("hello")
    assert result.result_hash.startswith("0x")
    assert len(result.result_hash) == 66  # 0x + 64 hex chars
