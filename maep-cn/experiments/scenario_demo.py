"""MAEP-CN End-to-end scenario demo — happy path + dispute path."""

import sys
import time

from agent_sdk.config import load_config
from agent_sdk.llm_client import LLMClient
from agent_sdk.db import DBClient
from agent_sdk.requester import RequesterAgent
from agent_sdk.provider import ProviderAgent
from agent_sdk.auditor import AuditorAgent


def fmt(cents: int) -> str:
    return f"RMB {cents / 100:.2f}"


def run_happy_path(requester, provider, db):
    print("\n" + "=" * 60)
    print("Scenario A: Happy Path")
    print("=" * 60)

    budget = 1000  # ¥10
    req_before = db.get_agent(requester.agent_id)
    prov_before = db.get_agent(provider.agent_id)

    t0 = time.perf_counter()
    session = requester.create_task("translation", "将以下句子翻译为英文：你好世界", budget)
    t1 = time.perf_counter()
    print(f"  [DELEGATE]  task_id={session.task_id}  budget={fmt(budget)}  ({(t1-t0)*1000:.1f}ms)")
    print(f"  Requester balance: {fmt(db.get_agent(requester.agent_id)['balance_cents'])}")

    session = provider.execute_task(session)
    t2 = time.perf_counter()
    print(f"  [EXECUTE]   result_hash={session.result.result_hash[:20]}...  ({(t2-t1)*1000:.1f}ms)")
    print(f"  Result: {session.result.result_data[:60]}...")

    accepted = requester.verify_result(session)
    t3 = time.perf_counter()
    print(f"  [VERIFY]    accepted={accepted}  ({(t3-t2)*1000:.1f}ms)")

    session.settle(accepted)
    db.settle_task(session.task_id, accepted)
    t4 = time.perf_counter()
    print(f"  [SETTLE]    stage={session.stage.value}  ({(t4-t3)*1000:.1f}ms)")

    req_after = db.get_agent(requester.agent_id)
    prov_after = db.get_agent(provider.agent_id)
    print(f"\n  Balance changes:")
    print(f"    Requester: {fmt(req_before['balance_cents'])} → {fmt(req_after['balance_cents'])}")
    print(f"    Provider:  {fmt(prov_before['balance_cents'])} → {fmt(prov_after['balance_cents'])}")
    print(f"  Total time: {(t4-t0)*1000:.1f}ms")

    return session


def run_dispute_path(requester, provider, auditor, db):
    print("\n" + "=" * 60)
    print("Scenario B: Dispute Path")
    print("=" * 60)

    budget = 500  # ¥5
    req_before = db.get_agent(requester.agent_id)
    prov_before = db.get_agent(provider.agent_id)

    t0 = time.perf_counter()
    session = requester.create_task("analysis", "分析这组数据趋势并给出结论", budget)
    t1 = time.perf_counter()
    print(f"  [DELEGATE]  task_id={session.task_id}  budget={fmt(budget)}  ({(t1-t0)*1000:.1f}ms)")

    session = provider.execute_task(session)
    t2 = time.perf_counter()
    print(f"  [EXECUTE]   ({(t2-t1)*1000:.1f}ms)")

    session.settle(accepted=False)
    db.settle_task(session.task_id, accepted=False)
    t3 = time.perf_counter()
    print(f"  [SETTLE]    stage=disputed  ({(t3-t2)*1000:.1f}ms)")

    ruling = auditor.arbitrate(session)
    t4 = time.perf_counter()
    print(f"  [ARBITRATE] ruling={ruling}  ({(t4-t3)*1000:.1f}ms)")

    req_after = db.get_agent(requester.agent_id)
    prov_after = db.get_agent(provider.agent_id)
    print(f"\n  Balance changes:")
    print(f"    Requester: {fmt(req_before['balance_cents'])} → {fmt(req_after['balance_cents'])}")
    print(f"    Provider:  {fmt(prov_before['balance_cents'])} → {fmt(prov_after['balance_cents'])}")
    print(f"  Total time: {(t4-t0)*1000:.1f}ms")


def main():
    try:
        config = load_config()
        llm = LLMClient(config)
        # Test connectivity
        llm.complete("Say OK")
        print("LLM connected successfully")
    except Exception as e:
        print(f"LLM unavailable ({type(e).__name__}), using mock LLM")
        llm = None

    db = DBClient(":memory:")

    deposit = 100_000  # ¥1000

    print("Registering agents with deposit =", fmt(deposit))
    db.register_agent("requester-1", "Requester", "translation,analysis", deposit)
    db.register_agent("provider-1", "Provider", "translation,analysis", deposit)
    db.register_agent("auditor-1", "Auditor", "audit", deposit)

    if llm:
        requester = RequesterAgent("requester-1", llm, db)
        provider = ProviderAgent("provider-1", llm, db)
        auditor = AuditorAgent("auditor-1", llm, db)
    else:
        # Fallback mock agents
        from agent_sdk.protocol import MAEPSession, TaskResult, TaskSpec, Stage

        class MockRequester(RequesterAgent):
            def __init__(self, aid, db):
                self.agent_id = aid
                self._llm = None
                self._db = db

            def create_task(self, task_type, desc, budget):
                task_id = f"{self.agent_id}-{task_type}-{budget}"
                spec = TaskSpec(task_type=task_type, description=desc, budget_cents=budget)
                s = MAEPSession(task_id=task_id)
                s.delegate(spec)
                self._db.create_task(task_id, self.agent_id, task_type, desc, budget)
                return s

            def verify_result(self, session):
                return True

        class MockProvider(ProviderAgent):
            def __init__(self, aid, db):
                self.agent_id = aid
                self._llm = None
                self._db = db

            def execute_task(self, session):
                result = TaskResult.from_data("Mock result: " + session.spec.description)
                session.execute(result)
                self._db.submit_result(session.task_id, self.agent_id,
                                       result.result_data, result.result_hash)
                return session

        class MockAuditor(AuditorAgent):
            def __init__(self, aid, db):
                self.agent_id = aid
                self._llm = None
                self._db = db

            def arbitrate(self, session):
                self._db.arbitrate_task(session.task_id, "PROVIDER")
                return "PROVIDER"

        requester = MockRequester("requester-1", db)
        provider = MockProvider("provider-1", db)
        auditor = MockAuditor("auditor-1", db)

    run_happy_path(requester, provider, db)
    run_dispute_path(requester, provider, auditor, db)

    stats = db.get_stats()
    print("\n" + "=" * 60)
    print("Platform Stats")
    print("=" * 60)
    print(f"  Agents: {stats['total_agents']}")
    print(f"  Tasks:  {stats['total_tasks']}")
    print(f"  Volume: {fmt(stats['total_volume_cents'])}")
    print(f"  Active: {stats['active_tasks']}")

    db.close()


if __name__ == "__main__":
    main()
