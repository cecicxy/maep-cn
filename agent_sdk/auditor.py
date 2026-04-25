from agent_sdk.protocol import MAEPSession, Stage
from agent_sdk.llm_client import LLMClient

class AuditorAgent:
    def __init__(self, agent_id: str, llm_client: LLMClient):
        self.agent_id = agent_id
        self._llm = llm_client

    def arbitrate(self, session: MAEPSession) -> str:
        if session.stage != Stage.DISPUTED:
            raise ValueError("Task not in DISPUTED stage")
        prompt = (
            f"Task description: {session.spec.description}\n"
            f"Provider result: {session.result.result_data}\n"
            "As an impartial auditor, rule in favor of REQUESTER or PROVIDER. Reply with one word."
        )
        ruling = self._llm.complete(prompt).strip().upper()
        return "PROVIDER" if "PROVIDER" in ruling else "REQUESTER"
