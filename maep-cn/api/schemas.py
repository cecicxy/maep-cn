"""Pydantic request/response schemas for MAEP-CN API."""

from pydantic import BaseModel, Field
from typing import Optional


# ── Requests ─────────────────────────────────────────────────────

class AgentCreateRequest(BaseModel):
    id: str
    name: str
    capabilities: str = ""
    initial_deposit_cents: int = Field(default=1000, ge=1000)

class TopupRequest(BaseModel):
    amount_cents: int = Field(gt=0)

class TaskCreateRequest(BaseModel):
    requester_id: str
    task_type: str
    description: str
    budget_cents: int = Field(gt=0)
    provider_id: Optional[str] = None

class ExecuteRequest(BaseModel):
    provider_id: str
    result_data: str

class VerifyRequest(BaseModel):
    accepted: bool

class DisputeRequest(BaseModel):
    disputed_by: str

class ArbitrateRequest(BaseModel):
    auditor_id: str


# ── Responses ────────────────────────────────────────────────────

class AgentResponse(BaseModel):
    id: str
    name: str
    capabilities: str
    reputation: int
    balance_cents: int
    active: int
    created_at: str

class TaskResponse(BaseModel):
    task_id: str
    requester_id: str
    provider_id: Optional[str]
    stage: str
    task_type: str
    description: str
    budget_cents: int
    result_data: Optional[str]
    result_hash: Optional[str]
    created_at: str
    updated_at: Optional[str]

class PaymentResponse(BaseModel):
    task_id: str
    from_agent: str
    to_agent: Optional[str]
    amount_cents: int
    status: str
    settled_at: Optional[str]

class StatsResponse(BaseModel):
    total_agents: int
    total_tasks: int
    total_volume_cents: int
    active_tasks: int

class MessageResponse(BaseModel):
    message: str
