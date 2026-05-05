from agent_sdk.protocol import MAEPSession, TaskSpec, Stage
from agent_sdk.llm_client import LLMClient
from agent_sdk.db import DBClient


class RequesterAgent:
    def __init__(self, agent_id: str, llm_client: LLMClient, db: DBClient):
        self.agent_id = agent_id
        self._llm = llm_client
        self._db = db

    def create_task(self, task_type: str, description: str, budget_cents: int) -> MAEPSession:
        task_id = f"{self.agent_id}-{task_type}-{budget_cents}"
        spec = TaskSpec(task_type=task_type, description=description, budget_cents=budget_cents)
        session = MAEPSession(task_id=task_id)
        session.delegate(spec)
        self._db.create_task(
            task_id=task_id,
            requester_id=self.agent_id,
            task_type=task_type,
            description=description,
            budget_cents=budget_cents,
        )
        return session

    def verify_result(self, session: MAEPSession) -> bool:
        if session.stage != Stage.EXECUTED:
            raise ValueError("No result to verify")
        prompt = (
            f"Task: {session.spec.description}\n"
            f"Result: {session.result.result_data}\n"
            "Is this result satisfactory? Reply YES or NO."
        )
        answer = self._llm.complete(prompt).strip().upper()
        return answer.startswith("YES")
