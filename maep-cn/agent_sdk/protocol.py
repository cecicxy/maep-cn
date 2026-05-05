"""MAEP protocol state machine — China domestic version (RMB cents)."""

from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
from typing import Optional


class Stage(Enum):
    REGISTERED = "registered"
    DELEGATED = "delegated"
    EXECUTED = "executed"
    SETTLED = "settled"
    DISPUTED = "disputed"


@dataclass
class TaskSpec:
    task_type: str
    description: str
    budget_cents: int


@dataclass
class TaskResult:
    result_data: str
    result_hash: str

    @classmethod
    def from_data(cls, data: str) -> "TaskResult":
        h = sha256(data.encode()).hexdigest()
        return cls(result_data=data, result_hash=f"0x{h}")


@dataclass
class MAEPSession:
    task_id: str
    stage: Stage = Stage.REGISTERED
    spec: Optional[TaskSpec] = None
    result: Optional[TaskResult] = None

    def delegate(self, spec: TaskSpec) -> None:
        if self.stage != Stage.REGISTERED:
            raise ValueError(f"Cannot delegate from stage {self.stage.value}")
        self.spec = spec
        self.stage = Stage.DELEGATED

    def execute(self, result: TaskResult) -> None:
        if self.stage != Stage.DELEGATED:
            raise ValueError(f"Cannot execute from stage {self.stage.value}")
        self.result = result
        self.stage = Stage.EXECUTED

    def settle(self, accepted: bool) -> None:
        if self.stage != Stage.EXECUTED:
            raise ValueError(f"Cannot settle from stage {self.stage.value}")
        self.stage = Stage.SETTLED if accepted else Stage.DISPUTED
