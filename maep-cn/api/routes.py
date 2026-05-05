"""MAEP-CN API routes."""

from fastapi import APIRouter, HTTPException, Request
from hashlib import sha256

from api.schemas import (
    AgentCreateRequest, AgentResponse, TopupRequest,
    TaskCreateRequest, TaskResponse, ExecuteRequest,
    VerifyRequest, DisputeRequest, ArbitrateRequest,
    PaymentResponse, StatsResponse, MessageResponse,
)
from agent_sdk.db import DBClient

router = APIRouter(prefix="/api")


def _get_db(request: Request) -> DBClient:
    return request.app.state.db


# ── Agent endpoints ──────────────────────────────────────────────

@router.post("/agents", response_model=AgentResponse, status_code=201)
async def create_agent(req: AgentCreateRequest, request: Request):
    db = _get_db(request)
    try:
        agent = db.register_agent(req.id, req.name, req.capabilities, req.initial_deposit_cents)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return agent


@router.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str, request: Request):
    db = _get_db(request)
    agent = db.get_agent(agent_id)
    if agent is None:
        raise HTTPException(404, f"Agent {agent_id} not found")
    return agent


@router.post("/agents/{agent_id}/topup", response_model=AgentResponse)
async def topup_agent(agent_id: str, req: TopupRequest, request: Request):
    db = _get_db(request)
    if db.get_agent(agent_id) is None:
        raise HTTPException(404, f"Agent {agent_id} not found")
    try:
        return db.topup_agent(agent_id, req.amount_cents)
    except ValueError as e:
        raise HTTPException(400, str(e))


# ── Task endpoints ───────────────────────────────────────────────

@router.post("/tasks", response_model=TaskResponse, status_code=201)
async def create_task(req: TaskCreateRequest, request: Request):
    db = _get_db(request)
    task_id = f"{req.requester_id}-{req.task_type}-{req.budget_cents}-{sha256(str(id(req)).encode()).hexdigest()[:8]}"
    try:
        task = db.create_task(
            task_id=task_id,
            requester_id=req.requester_id,
            task_type=req.task_type,
            description=req.description,
            budget_cents=req.budget_cents,
            provider_id=req.provider_id,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    return task


@router.get("/tasks", response_model=list[TaskResponse])
async def list_tasks(request: Request, limit: int = 20):
    db = _get_db(request)
    return db.list_tasks(limit)


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, request: Request):
    db = _get_db(request)
    task = db.get_task(task_id)
    if task is None:
        raise HTTPException(404, f"Task {task_id} not found")
    return task


@router.post("/tasks/{task_id}/execute", response_model=TaskResponse)
async def execute_task(task_id: str, req: ExecuteRequest, request: Request):
    db = _get_db(request)
    result_hash = "0x" + sha256(req.result_data.encode()).hexdigest()
    try:
        return db.submit_result(task_id, req.provider_id, req.result_data, result_hash)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/tasks/{task_id}/verify", response_model=MessageResponse)
async def verify_task(task_id: str, req: VerifyRequest, request: Request):
    db = _get_db(request)
    try:
        task = db.settle_task(task_id, req.accepted)
    except ValueError as e:
        raise HTTPException(400, str(e))
    stage = task["stage"]
    return MessageResponse(message=f"Task {task_id} is now {stage}")


@router.post("/tasks/{task_id}/dispute", response_model=TaskResponse)
async def dispute_task(task_id: str, req: DisputeRequest, request: Request):
    db = _get_db(request)
    try:
        return db.dispute_task(task_id, req.disputed_by)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/tasks/{task_id}/arbitrate", response_model=MessageResponse)
async def arbitrate_task(task_id: str, req: ArbitrateRequest, request: Request):
    db = _get_db(request)
    task = db.get_task(task_id)
    if task is None:
        raise HTTPException(404, f"Task {task_id} not found")
    payment = db.get_payment(task_id)
    if payment is None:
        raise HTTPException(404, f"Payment for task {task_id} not found")
    ruling = "PROVIDER" if payment["to_agent"] == task.get("provider_id") else "REQUESTER"
    try:
        db.arbitrate_task(task_id, ruling)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return MessageResponse(message=f"Arbitration complete: ruling for {ruling}")


# ── Stats ────────────────────────────────────────────────────────

@router.get("/stats", response_model=StatsResponse)
async def get_stats(request: Request):
    db = _get_db(request)
    return db.get_stats()
