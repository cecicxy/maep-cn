"""
Experiment 4: 3-agent end-to-end scenario demo.
Requires: .env with LLM_PROVIDER, LLM_API_KEY, LLM_MODEL set.
Run: python experiments/scenario_demo.py
"""
import json
import time
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_sdk.config import load_config
from agent_sdk.llm_client import LLMClient
from agent_sdk.requester import RequesterAgent
from agent_sdk.provider import ProviderAgent
from agent_sdk.auditor import AuditorAgent
from agent_sdk.protocol import Stage


def run_happy_path(requester, provider):
    print("\n--- Scenario A: Happy Path ---")
    session = requester.create_task(
        task_type="data_analysis",
        description="Analyze this dataset summary: 100 users, avg age 32, 60% male. Provide 3 key insights.",
        budget_wei=10**15,
    )
    print(f"  [DELEGATE] Task created: {session.task_id}")
    print(f"  [DELEGATE] Stage: {session.stage.value}")

    session = provider.execute_task(session)
    print(f"  [EXECUTE]  Result: {session.result.result_data[:100]}...")
    print(f"  [EXECUTE]  Hash: {session.result.result_hash[:20]}...")

    accepted = requester.verify_result(session)
    session.settle(accepted=accepted)
    print(f"  [SETTLE]   Accepted: {accepted}, Stage: {session.stage.value}")
    return session


def run_dispute_path(requester, provider, auditor):
    print("\n--- Scenario B: Dispute Path ---")
    session = requester.create_task(
        task_type="data_analysis",
        description="Analyze: empty dataset. Report findings.",
        budget_wei=10**15,
    )
    print(f"  [DELEGATE] Task created: {session.task_id}")

    session = provider.execute_task(session)
    print(f"  [EXECUTE]  Result: {session.result.result_data[:80]}...")

    # Force rejection for demo
    session.settle(accepted=False)
    print(f"  [SETTLE]   Rejected -> Stage: {session.stage.value}")

    ruling = auditor.arbitrate(session)
    print(f"  [DISPUTE]  Auditor ruling: {ruling}")
    return session, ruling


if __name__ == "__main__":
    try:
        cfg = load_config()
    except ValueError as e:
        print(f"ERROR: {e}")
        print("Please copy .env.example to .env and set your LLM credentials.")
        sys.exit(1)

    print(f"LLM Provider: {cfg['provider']} | Model: {cfg['model']}")

    llm = LLMClient(cfg)
    requester = RequesterAgent("requester-001", llm)
    provider = ProviderAgent("provider-001", llm)
    auditor = AuditorAgent("auditor-001", llm)

    results = {}

    t0 = time.time()
    session_a = run_happy_path(requester, provider)
    results["scenario_a"] = {
        "stage": session_a.stage.value,
        "duration_s": round(time.time() - t0, 2),
    }

    t1 = time.time()
    session_b, ruling = run_dispute_path(requester, provider, auditor)
    results["scenario_b"] = {
        "stage": session_b.stage.value,
        "ruling": ruling,
        "duration_s": round(time.time() - t1, 2),
    }

    print(f"\n=== Summary ===")
    print(json.dumps(results, indent=2))

    os.makedirs("experiments", exist_ok=True)
    with open("experiments/results_scenario.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nResults saved to experiments/results_scenario.json")
