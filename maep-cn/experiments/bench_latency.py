"""MAEP-CN latency benchmark — protocol overhead + DB operation latency."""

import time
import statistics
from hashlib import sha256

from agent_sdk.protocol import MAEPSession, TaskSpec, TaskResult
from agent_sdk.db import DBClient


def bench_protocol_overhead(n=10000):
    print("\nTable 1: Protocol Stage Overhead (microseconds)")
    print("-" * 55)
    print(f"{'Operation':<25} {'Mean':>10} {'Median':>10} {'Stdev':>10}")
    print("-" * 55)

    # Delegate
    times = []
    for i in range(n):
        session = MAEPSession(task_id=f"t-{i}")
        spec = TaskSpec(task_type="test", description="bench", budget_cents=100)
        t0 = time.perf_counter_ns()
        session.delegate(spec)
        t1 = time.perf_counter_ns()
        times.append((t1 - t0) / 1000)

    print(f"{'delegate()':<25} {statistics.mean(times):>10.2f} "
          f"{statistics.median(times):>10.2f} {statistics.stdev(times):>10.2f}")

    # Execute
    times = []
    for i in range(n):
        session = MAEPSession(task_id=f"t-{i}")
        spec = TaskSpec(task_type="test", description="bench", budget_cents=100)
        session.delegate(spec)
        t0 = time.perf_counter_ns()
        result = TaskResult.from_data("benchmark result data")
        session.execute(result)
        t1 = time.perf_counter_ns()
        times.append((t1 - t0) / 1000)

    print(f"{'execute()':<25} {statistics.mean(times):>10.2f} "
          f"{statistics.median(times):>10.2f} {statistics.stdev(times):>10.2f}")

    # Settle
    times = []
    for i in range(n):
        session = MAEPSession(task_id=f"t-{i}")
        spec = TaskSpec(task_type="test", description="bench", budget_cents=100)
        session.delegate(spec)
        result = TaskResult.from_data("benchmark result data")
        session.execute(result)
        t0 = time.perf_counter_ns()
        session.settle(True)
        t1 = time.perf_counter_ns()
        times.append((t1 - t0) / 1000)

    print(f"{'settle()':<25} {statistics.mean(times):>10.2f} "
          f"{statistics.median(times):>10.2f} {statistics.stdev(times):>10.2f}")

    # Baseline: bare Python operations
    times = []
    for i in range(n):
        t0 = time.perf_counter_ns()
        _ = {"type": "test", "desc": "bench", "budget": 100}
        _ = "0x" + sha256(b"benchmark result data").hexdigest()
        _ = True
        t1 = time.perf_counter_ns()
        times.append((t1 - t0) / 1000)

    print(f"{'baseline (dict+hash)':<25} {statistics.mean(times):>10.2f} "
          f"{statistics.median(times):>10.2f} {statistics.stdev(times):>10.2f}")


def bench_db_operations(n=500):
    print(f"\nTable 2: Database Operation Latency (microseconds, n={n})")
    print("-" * 55)
    print(f"{'Operation':<25} {'Mean':>10} {'Median':>10} {'Stdev':>10}")
    print("-" * 55)

    db = DBClient(":memory:")
    db.register_agent("bench-req", "BenchReq", "test", 10_000_000)
    db.register_agent("bench-prov", "BenchProv", "test", 10_000_000)

    # create_task
    times = []
    for i in range(n):
        tid = f"task-{i}"
        t0 = time.perf_counter_ns()
        db.create_task(tid, "bench-req", "test", "bench task", 100, "bench-prov")
        t1 = time.perf_counter_ns()
        times.append((t1 - t0) / 1000)

    print(f"{'create_task()':<25} {statistics.mean(times):>10.1f} "
          f"{statistics.median(times):>10.1f} {statistics.stdev(times):>10.1f}")

    # submit_result
    times = []
    for i in range(n):
        tid = f"exec-{i}"
        db.create_task(tid, "bench-req", "test", "bench task", 100, "bench-prov")
        rh = "0x" + sha256(f"result-{i}".encode()).hexdigest()
        t0 = time.perf_counter_ns()
        db.submit_result(tid, "bench-prov", f"result-{i}", rh)
        t1 = time.perf_counter_ns()
        times.append((t1 - t0) / 1000)

    print(f"{'submit_result()':<25} {statistics.mean(times):>10.1f} "
          f"{statistics.median(times):>10.1f} {statistics.stdev(times):>10.1f}")

    # settle_task (accepted)
    times = []
    for i in range(n):
        tid = f"settle-{i}"
        db.create_task(tid, "bench-req", "test", "bench task", 100, "bench-prov")
        rh = "0x" + sha256(f"result-{i}".encode()).hexdigest()
        db.submit_result(tid, "bench-prov", f"result-{i}", rh)
        t0 = time.perf_counter_ns()
        db.settle_task(tid, True)
        t1 = time.perf_counter_ns()
        times.append((t1 - t0) / 1000)

    print(f"{'settle_task()':<25} {statistics.mean(times):>10.1f} "
          f"{statistics.median(times):>10.1f} {statistics.stdev(times):>10.1f}")

    # arbitrate_task
    times = []
    for i in range(n):
        tid = f"arb-{i}"
        db.create_task(tid, "bench-req", "test", "bench task", 100, "bench-prov")
        rh = "0x" + sha256(f"result-{i}".encode()).hexdigest()
        db.submit_result(tid, "bench-prov", f"result-{i}", rh)
        db.settle_task(tid, False)
        db.dispute_task(tid, "bench-req")
        t0 = time.perf_counter_ns()
        db.arbitrate_task(tid, "PROVIDER")
        t1 = time.perf_counter_ns()
        times.append((t1 - t0) / 1000)

    print(f"{'arbitrate_task()':<25} {statistics.mean(times):>10.1f} "
          f"{statistics.median(times):>10.1f} {statistics.stdev(times):>10.1f}")

    db.close()


if __name__ == "__main__":
    bench_protocol_overhead()
    bench_db_operations()
