import pytest
from agent_sdk.protocol import MAEPSession, Stage, TaskSpec, TaskResult

def test_initial_stage():
    session = MAEPSession(task_id="task-001")
    assert session.stage == Stage.REGISTERED

def test_full_happy_path():
    session = MAEPSession(task_id="task-001")
    spec = TaskSpec(task_type="data_analysis", description="Analyze CSV", budget_wei=100)
    session.delegate(spec)
    assert session.stage == Stage.DELEGATED

    result = TaskResult(result_data="summary: 42 rows", result_hash="0xabc")
    session.execute(result)
    assert session.stage == Stage.EXECUTED

    session.settle(accepted=True)
    assert session.stage == Stage.SETTLED

def test_cannot_skip_stages():
    session = MAEPSession(task_id="task-002")
    result = TaskResult(result_data="data", result_hash="0xdef")
    with pytest.raises(ValueError, match="Cannot execute"):
        session.execute(result)

def test_settle_rejected_goes_to_dispute():
    session = MAEPSession(task_id="task-003")
    spec = TaskSpec(task_type="data_analysis", description="Analyze", budget_wei=50)
    session.delegate(spec)
    result = TaskResult(result_data="bad result", result_hash="0x000")
    session.execute(result)
    session.settle(accepted=False)
    assert session.stage == Stage.DISPUTED
