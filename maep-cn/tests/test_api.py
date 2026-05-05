"""Tests for MAEP-CN FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient

from api.app import create_app
from agent_sdk.db import DBClient


@pytest.fixture
def client():
    app = create_app(db_path=":memory:")
    with TestClient(app) as c:
        yield c


def _register(client, agent_id, name="Agent", deposit=10000):
    return client.post("/api/agents", json={
        "id": agent_id, "name": name,
        "capabilities": "test", "initial_deposit_cents": deposit,
    })


def test_register_agent(client):
    res = _register(client, "a1")
    assert res.status_code == 201
    data = res.json()
    assert data["id"] == "a1"
    assert data["balance_cents"] == 10000


def test_register_insufficient(client):
    res = _register(client, "a2", deposit=100)
    assert res.status_code == 422  # Pydantic rejects < 1000 before reaching DB


def test_get_agent(client):
    _register(client, "a1")
    res = client.get("/api/agents/a1")
    assert res.status_code == 200
    assert res.json()["name"] == "Agent"


def test_get_agent_not_found(client):
    res = client.get("/api/agents/nonexistent")
    assert res.status_code == 404


def test_topup(client):
    _register(client, "a1")
    res = client.post("/api/agents/a1/topup", json={"amount_cents": 5000})
    assert res.status_code == 200
    assert res.json()["balance_cents"] == 15000


def test_create_task(client):
    _register(client, "req")
    _register(client, "prov")
    res = client.post("/api/tasks", json={
        "requester_id": "req", "task_type": "test",
        "description": "test task", "budget_cents": 1000,
        "provider_id": "prov",
    })
    assert res.status_code == 201
    data = res.json()
    assert data["stage"] == "delegated"
    assert data["budget_cents"] == 1000
    # Check balance deducted
    assert client.get("/api/agents/req").json()["balance_cents"] == 9000


def test_create_task_insufficient(client):
    _register(client, "req", deposit=1000)
    res = client.post("/api/tasks", json={
        "requester_id": "req", "task_type": "test",
        "description": "test task", "budget_cents": 5000,
    })
    assert res.status_code == 400


def test_execute_task(client):
    _register(client, "req")
    _register(client, "prov")
    task = client.post("/api/tasks", json={
        "requester_id": "req", "task_type": "test",
        "description": "test task", "budget_cents": 1000,
        "provider_id": "prov",
    }).json()
    res = client.post(f"/api/tasks/{task['task_id']}/execute", json={
        "provider_id": "prov", "result_data": "Hello World",
    })
    assert res.status_code == 200
    assert res.json()["stage"] == "executed"


def test_verify_accept(client):
    _register(client, "req")
    _register(client, "prov")
    task = client.post("/api/tasks", json={
        "requester_id": "req", "task_type": "test",
        "description": "test task", "budget_cents": 1000,
        "provider_id": "prov",
    }).json()
    client.post(f"/api/tasks/{task['task_id']}/execute", json={
        "provider_id": "prov", "result_data": "result",
    })
    res = client.post(f"/api/tasks/{task['task_id']}/verify", json={"accepted": True})
    assert res.status_code == 200
    assert "settled" in res.json()["message"]
    assert client.get("/api/agents/prov").json()["balance_cents"] == 11000


def test_verify_reject_and_dispute(client):
    _register(client, "req")
    _register(client, "prov")
    task = client.post("/api/tasks", json={
        "requester_id": "req", "task_type": "test",
        "description": "test task", "budget_cents": 1000,
        "provider_id": "prov",
    }).json()
    client.post(f"/api/tasks/{task['task_id']}/execute", json={
        "provider_id": "prov", "result_data": "result",
    })
    res = client.post(f"/api/tasks/{task['task_id']}/verify", json={"accepted": False})
    assert "disputed" in res.json()["message"]


def test_stats(client):
    _register(client, "a1")
    _register(client, "a2")
    res = client.get("/api/stats")
    assert res.status_code == 200
    data = res.json()
    assert data["total_agents"] == 2


def test_list_tasks(client):
    _register(client, "req", deposit=100000)
    for i in range(5):
        client.post("/api/tasks", json={
            "requester_id": "req", "task_type": "test",
            "description": f"task {i}", "budget_cents": 100,
        })
    res = client.get("/api/tasks?limit=3")
    assert res.status_code == 200
    assert len(res.json()) == 3
