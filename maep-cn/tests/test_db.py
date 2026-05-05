"""Tests for DBClient — all contract logic replicated in SQLite."""

import pytest
from agent_sdk.db import DBClient


@pytest.fixture
def db():
    client = DBClient(":memory:")
    yield client
    client.close()


def test_register_agent(db):
    agent = db.register_agent("a1", "Agent One", "translation", 1000)
    assert agent["id"] == "a1"
    assert agent["name"] == "Agent One"
    assert agent["capabilities"] == "translation"
    assert agent["reputation"] == 100
    assert agent["balance_cents"] == 1000
    assert agent["active"] == 1


def test_register_insufficient_deposit(db):
    with pytest.raises(ValueError, match="Minimum deposit"):
        db.register_agent("a1", "Agent", "test", 500)


def test_topup(db):
    db.register_agent("a1", "Agent", "test", 1000)
    agent = db.topup_agent("a1", 5000)
    assert agent["balance_cents"] == 6000


def test_topup_negative(db):
    db.register_agent("a1", "Agent", "test", 1000)
    with pytest.raises(ValueError, match="positive"):
        db.topup_agent("a1", -100)


def test_create_task_locks_balance(db):
    db.register_agent("req", "Requester", "test", 10000)
    db.register_agent("prov", "Provider", "test", 10000)
    task = db.create_task("t1", "req", "translation", "translate text", 1000, "prov")
    assert task["stage"] == "delegated"
    assert task["budget_cents"] == 1000
    req = db.get_agent("req")
    assert req["balance_cents"] == 9000

    payment = db.get_payment("t1")
    assert payment["status"] == "locked"
    assert payment["amount_cents"] == 1000
    assert payment["from_agent"] == "req"


def test_create_task_insufficient_balance(db):
    db.register_agent("req", "Requester", "test", 1000)
    with pytest.raises(ValueError, match="Insufficient"):
        db.create_task("t1", "req", "test", "task", 5000)


def test_submit_result(db):
    db.register_agent("req", "Requester", "test", 10000)
    db.register_agent("prov", "Provider", "test", 10000)
    db.create_task("t1", "req", "test", "task", 1000, "prov")
    task = db.submit_result("t1", "prov", "Hello World", "0xabc")
    assert task["stage"] == "executed"
    assert task["provider_id"] == "prov"
    assert task["result_data"] == "Hello World"


def test_submit_result_wrong_stage(db):
    db.register_agent("req", "Requester", "test", 10000)
    db.register_agent("prov", "Provider", "test", 10000)
    db.create_task("t1", "req", "test", "task", 1000, "prov")
    db.submit_result("t1", "prov", "result", "0xabc")
    with pytest.raises(ValueError, match="expected 'delegated'"):
        db.submit_result("t1", "prov", "result2", "0xdef")


def test_settle_accepted_releases_payment(db):
    db.register_agent("req", "Requester", "test", 10000)
    db.register_agent("prov", "Provider", "test", 10000)
    db.create_task("t1", "req", "test", "task", 1000, "prov")
    db.submit_result("t1", "prov", "result", "0xabc")
    task = db.settle_task("t1", True)
    assert task["stage"] == "settled"
    assert db.get_agent("prov")["balance_cents"] == 11000
    assert db.get_agent("req")["balance_cents"] == 9000
    assert db.get_payment("t1")["status"] == "released"


def test_settle_rejected_disputed(db):
    db.register_agent("req", "Requester", "test", 10000)
    db.register_agent("prov", "Provider", "test", 10000)
    db.create_task("t1", "req", "test", "task", 1000, "prov")
    db.submit_result("t1", "prov", "result", "0xabc")
    task = db.settle_task("t1", False)
    assert task["stage"] == "disputed"
    # Balance unchanged during dispute
    assert db.get_agent("prov")["balance_cents"] == 10000
    assert db.get_agent("req")["balance_cents"] == 9000


def test_dispute(db):
    db.register_agent("req", "Requester", "test", 10000)
    db.register_agent("prov", "Provider", "test", 10000)
    db.create_task("t1", "req", "test", "task", 1000, "prov")
    db.submit_result("t1", "prov", "result", "0xabc")
    db.settle_task("t1", False)
    task = db.dispute_task("t1", "req")
    assert task["stage"] == "disputed"


def test_arbitrate_provider_wins(db):
    db.register_agent("req", "Requester", "test", 10000)
    db.register_agent("prov", "Provider", "test", 10000)
    db.create_task("t1", "req", "test", "task", 1000, "prov")
    db.submit_result("t1", "prov", "result", "0xabc")
    db.settle_task("t1", False)
    db.dispute_task("t1", "req")
    task = db.arbitrate_task("t1", "PROVIDER")
    assert task["stage"] == "settled"
    assert db.get_agent("prov")["balance_cents"] == 11000
    assert db.get_agent("req")["balance_cents"] == 9000


def test_arbitrate_requester_wins(db):
    db.register_agent("req", "Requester", "test", 10000)
    db.register_agent("prov", "Provider", "test", 10000)
    db.create_task("t1", "req", "test", "task", 1000, "prov")
    db.submit_result("t1", "prov", "result", "0xabc")
    db.settle_task("t1", False)
    db.dispute_task("t1", "req")
    task = db.arbitrate_task("t1", "REQUESTER")
    assert task["stage"] == "settled"
    assert db.get_agent("req")["balance_cents"] == 10000
    assert db.get_agent("prov")["balance_cents"] == 10000


def test_list_tasks_and_stats(db):
    db.register_agent("req", "Requester", "test", 100000)
    db.register_agent("prov", "Provider", "test", 100000)
    for i in range(5):
        db.create_task(f"t{i}", "req", "test", f"task {i}", 1000, "prov")
    tasks = db.list_tasks(limit=3)
    assert len(tasks) == 3
    stats = db.get_stats()
    assert stats["total_agents"] == 2
    assert stats["total_tasks"] == 5
    assert stats["active_tasks"] == 5
