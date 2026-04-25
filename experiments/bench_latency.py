"""
Experiment 1: End-to-end latency per MAEP stage.
Baseline: simulated plain HTTP A2A (no chain ops).
Run: python experiments/bench_latency.py
"""
import time
import statistics
import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_sdk.protocol import MAEPSession, TaskSpec, TaskResult

RUNS = 50

def time_stage(fn):
    start = time.perf_counter()
    fn()
    return (time.perf_counter() - start) * 1000  # ms

def run_maep_session():
    timings = {}
    session = MAEPSession(task_id="bench-task")

    spec = TaskSpec(task_type="data_analysis", description="Benchmark task", budget_wei=1000)
    timings["delegate_ms"] = time_stage(lambda: session.delegate(spec))

    result = TaskResult.from_data("benchmark result data")
    timings["execute_ms"] = time_stage(lambda: session.execute(result))

    timings["settle_ms"] = time_stage(lambda: session.settle(accepted=True))

    return timings

def baseline_http_a2a():
    timings = {}
    timings["delegate_ms"] = time_stage(lambda: {"task": "data_analysis", "budget": 1000})
    timings["execute_ms"] = time_stage(lambda: {"result": "done"})
    timings["settle_ms"] = time_stage(lambda: {"settled": True})
    return timings

if __name__ == "__main__":
    maep_results = [run_maep_session() for _ in range(RUNS)]
    baseline_results = [baseline_http_a2a() for _ in range(RUNS)]

    print(f"\n{'Stage':<15} {'MAEP mean(ms)':>15} {'Baseline mean(ms)':>18} {'Overhead':>10}")
    print("-" * 62)
    for stage in ["delegate_ms", "execute_ms", "settle_ms"]:
        maep_vals = [r[stage] for r in maep_results]
        base_vals = [r[stage] for r in baseline_results]
        maep_mean = statistics.mean(maep_vals)
        base_mean = statistics.mean(base_vals)
        overhead = f"{((maep_mean / base_mean - 1) * 100):.1f}%" if base_mean > 0 else "N/A"
        print(f"{stage:<15} {maep_mean:>15.4f} {base_mean:>18.4f} {overhead:>10}")

    out = {"maep": maep_results[:5], "baseline": baseline_results[:5], "runs": RUNS}
    with open("experiments/results_latency.json", "w") as f:
        json.dump(out, f, indent=2)
    print("\nSample results saved to experiments/results_latency.json")
