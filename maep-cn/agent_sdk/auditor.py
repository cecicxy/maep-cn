from agent_sdk.protocol import MAEPSession, Stage
from agent_sdk.llm_client import LLMClient
from agent_sdk.db import DBClient


class AuditorAgent:
    def __init__(self, agent_id: str, llm_client: LLMClient, db: DBClient):
        self.agent_id = agent_id
        self._llm = llm_client
        self._db = db

    def arbitrate(self, session: MAEPSession) -> str:
        if session.stage != Stage.DISPUTED:
            raise ValueError("Task not in DISPUTED stage")
        prompt = (
            f"Task description: {session.spec.description}\n"
            f"Provider result: {session.result.result_data}\n"
            "As an impartial auditor, rule in favor of REQUESTER or PROVIDER. Reply with one word."
        )
        ruling = self._llm.complete(prompt).strip().upper()
        ruling = "PROVIDER" if "PROVIDER" in ruling else "REQUESTER"
        self._db.arbitrate_task(session.task_id, ruling)
        return ruling
