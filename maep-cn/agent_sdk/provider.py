from agent_sdk.protocol import MAEPSession, TaskResult, Stage
from agent_sdk.llm_client import LLMClient
from agent_sdk.db import DBClient


class ProviderAgent:
    def __init__(self, agent_id: str, llm_client: LLMClient, db: DBClient):
        self.agent_id = agent_id
        self._llm = llm_client
        self._db = db

    def execute_task(self, session: MAEPSession) -> MAEPSession:
        if session.stage != Stage.DELEGATED:
            raise ValueError("Task not in DELEGATED stage")
        prompt = f"Complete this task: {session.spec.description}\nProvide a concise result."
        result_data = self._llm.complete(prompt)
        result = TaskResult.from_data(result_data)
        session.execute(result)
        self._db.submit_result(
            task_id=session.task_id,
            provider_id=self.agent_id,
            result_data=result_data,
            result_hash=result.result_hash,
        )
        return session
