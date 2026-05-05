"""SQLite storage client — replaces ChainClient + all three smart contracts."""

import sqlite3
from datetime import datetime, timezone
from typing import Optional


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class DBClient:
    def __init__(self, db_path: str = "maep.db", min_deposit_cents: int = 1000):
        self._db_path = db_path
        self._min_deposit = min_deposit_cents
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                capabilities TEXT NOT NULL DEFAULT '',
                reputation INTEGER NOT NULL DEFAULT 100,
                balance_cents INTEGER NOT NULL DEFAULT 0,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                requester_id TEXT NOT NULL REFERENCES agents(id),
                provider_id TEXT REFERENCES agents(id),
                stage TEXT NOT NULL DEFAULT 'delegated',
                task_type TEXT NOT NULL,
                description TEXT NOT NULL,
                budget_cents INTEGER NOT NULL,
                result_data TEXT,
                result_hash TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT
            );
            CREATE TABLE IF NOT EXISTS payments (
                task_id TEXT PRIMARY KEY REFERENCES tasks(task_id),
                from_agent TEXT NOT NULL REFERENCES agents(id),
                to_agent TEXT REFERENCES agents(id),
                amount_cents INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'locked',
                deadline TEXT,
                settled_at TEXT
            );
            CREATE TABLE IF NOT EXISTS attestations (
                task_id TEXT PRIMARY KEY REFERENCES tasks(task_id),
                provider_id TEXT NOT NULL REFERENCES agents(id),
                result_hash TEXT NOT NULL,
                disputed INTEGER NOT NULL DEFAULT 0,
                disputed_by TEXT,
                created_at TEXT NOT NULL
            );
        """)
        self._conn.commit()

    def close(self):
        self._conn.close()

    # ── Agent Registry ────────────────────────────────────────────

    def register_agent(self, agent_id: str, name: str, capabilities: str = "",
                       initial_deposit_cents: int = 0) -> dict:
        if initial_deposit_cents < self._min_deposit:
            raise ValueError(
                f"Minimum deposit is {self._min_deposit} cents, "
                f"got {initial_deposit_cents}"
            )
        now = _now()
        self._conn.execute(
            "INSERT INTO agents (id, name, capabilities, balance_cents, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (agent_id, name, capabilities, initial_deposit_cents, now),
        )
        self._conn.commit()
        return self.get_agent(agent_id)

    def get_agent(self, agent_id: str) -> Optional[dict]:
        row = self._conn.execute(
            "SELECT * FROM agents WHERE id = ?", (agent_id,)
        ).fetchone()
        if row is None:
            return None
        return dict(row)

    def topup_agent(self, agent_id: str, amount_cents: int) -> dict:
        if amount_cents <= 0:
            raise ValueError("Top-up amount must be positive")
        self._conn.execute(
            "UPDATE agents SET balance_cents = balance_cents + ? WHERE id = ?",
            (amount_cents, agent_id),
        )
        self._conn.commit()
        return self.get_agent(agent_id)

    def deregister_agent(self, agent_id: str) -> None:
        agent = self.get_agent(agent_id)
        if agent is None:
            raise ValueError(f"Agent {agent_id} not found")
        if not agent["active"]:
            raise ValueError(f"Agent {agent_id} already inactive")
        self._conn.execute(
            "UPDATE agents SET active = 0, balance_cents = 0 WHERE id = ?",
            (agent_id,),
        )
        self._conn.commit()

    def update_reputation(self, agent_id: str, new_reputation: int) -> dict:
        if not 0 <= new_reputation <= 10000:
            raise ValueError("Reputation must be 0-10000")
        self._conn.execute(
            "UPDATE agents SET reputation = ? WHERE id = ?",
            (new_reputation, agent_id),
        )
        self._conn.commit()
        return self.get_agent(agent_id)

    # ── Payment Channel (create + settle) ─────────────────────────

    def create_task(self, task_id: str, requester_id: str, task_type: str,
                    description: str, budget_cents: int,
                    provider_id: Optional[str] = None,
                    deadline_hours: int = 24) -> dict:
        now = _now()
        deadline = datetime.fromisoformat(now)  # not used in simplified version
        try:
            cur = self._conn.execute("BEGIN IMMEDIATE")
            row = self._conn.execute(
                "SELECT balance_cents FROM agents WHERE id = ? AND active = 1",
                (requester_id,),
            ).fetchone()
            if row is None:
                raise ValueError(f"Requester {requester_id} not found or inactive")
            if row["balance_cents"] < budget_cents:
                raise ValueError(
                    f"Insufficient balance: {row['balance_cents']} < {budget_cents}"
                )
            self._conn.execute(
                "UPDATE agents SET balance_cents = balance_cents - ? WHERE id = ?",
                (budget_cents, requester_id),
            )
            self._conn.execute(
                "INSERT INTO tasks "
                "(task_id, requester_id, provider_id, stage, task_type, description, "
                "budget_cents, created_at) VALUES (?, ?, ?, 'delegated', ?, ?, ?, ?)",
                (task_id, requester_id, provider_id, task_type, description,
                 budget_cents, now),
            )
            self._conn.execute(
                "INSERT INTO payments (task_id, from_agent, to_agent, amount_cents, "
                "status, deadline) VALUES (?, ?, ?, ?, 'locked', ?)",
                (task_id, requester_id, provider_id, budget_cents, now),
            )
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise
        return self.get_task(task_id)

    def get_task(self, task_id: str) -> Optional[dict]:
        row = self._conn.execute(
            "SELECT * FROM tasks WHERE task_id = ?", (task_id,)
        ).fetchone()
        if row is None:
            return None
        return dict(row)

    def get_payment(self, task_id: str) -> Optional[dict]:
        row = self._conn.execute(
            "SELECT * FROM payments WHERE task_id = ?", (task_id,)
        ).fetchone()
        return dict(row) if row else None

    # ── Result Attestation ────────────────────────────────────────

    def submit_result(self, task_id: str, provider_id: str,
                      result_data: str, result_hash: str) -> dict:
        now = _now()
        task = self.get_task(task_id)
        if task is None:
            raise ValueError(f"Task {task_id} not found")
        if task["stage"] != "delegated":
            raise ValueError(f"Task {task_id} is in stage '{task['stage']}', expected 'delegated'")
        try:
            self._conn.execute("BEGIN IMMEDIATE")
            self._conn.execute(
                "UPDATE tasks SET provider_id = ?, result_data = ?, result_hash = ?, "
                "stage = 'executed', updated_at = ? WHERE task_id = ?",
                (provider_id, result_data, result_hash, now, task_id),
            )
            self._conn.execute(
                "UPDATE payments SET to_agent = ? WHERE task_id = ?",
                (provider_id, task_id),
            )
            self._conn.execute(
                "INSERT INTO attestations (task_id, provider_id, result_hash, created_at) "
                "VALUES (?, ?, ?, ?)",
                (task_id, provider_id, result_hash, now),
            )
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise
        return self.get_task(task_id)

    def settle_task(self, task_id: str, accepted: bool) -> dict:
        task = self.get_task(task_id)
        if task is None:
            raise ValueError(f"Task {task_id} not found")
        if task["stage"] != "executed":
            raise ValueError(f"Task {task_id} is in stage '{task['stage']}', expected 'executed'")
        now = _now()
        try:
            self._conn.execute("BEGIN IMMEDIATE")
            if accepted:
                self._conn.execute(
                    "UPDATE payments SET status = 'released', settled_at = ? "
                    "WHERE task_id = ?",
                    (now, task_id),
                )
                if task["provider_id"]:
                    self._conn.execute(
                        "UPDATE agents SET balance_cents = balance_cents + ? "
                        "WHERE id = ?",
                        (task["budget_cents"], task["provider_id"]),
                    )
                self._conn.execute(
                    "UPDATE tasks SET stage = 'settled', updated_at = ? "
                    "WHERE task_id = ?",
                    (now, task_id),
                )
            else:
                self._conn.execute(
                    "UPDATE tasks SET stage = 'disputed', updated_at = ? "
                    "WHERE task_id = ?",
                    (now, task_id),
                )
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise
        return self.get_task(task_id)

    def dispute_task(self, task_id: str, disputed_by: str) -> dict:
        now = _now()
        task = self.get_task(task_id)
        if task is None:
            raise ValueError(f"Task {task_id} not found")
        if task["stage"] != "executed" and task["stage"] != "disputed":
            raise ValueError(f"Task {task_id} cannot be disputed from stage '{task['stage']}'")
        self._conn.execute(
            "UPDATE attestations SET disputed = 1, disputed_by = ? WHERE task_id = ?",
            (disputed_by, task_id),
        )
        if task["stage"] != "disputed":
            self._conn.execute(
                "UPDATE tasks SET stage = 'disputed', updated_at = ? WHERE task_id = ?",
                (now, task_id),
            )
        self._conn.commit()
        return self.get_task(task_id)

    def arbitrate_task(self, task_id: str, ruling: str) -> dict:
        """ruling: 'PROVIDER' or 'REQUESTER'."""
        if ruling not in ("PROVIDER", "REQUESTER"):
            raise ValueError("Ruling must be PROVIDER or REQUESTER")
        task = self.get_task(task_id)
        if task is None:
            raise ValueError(f"Task {task_id} not found")
        if task["stage"] != "disputed":
            raise ValueError(f"Task {task_id} is not disputed")
        now = _now()
        try:
            self._conn.execute("BEGIN IMMEDIATE")
            if ruling == "PROVIDER":
                self._conn.execute(
                    "UPDATE payments SET status = 'released', settled_at = ? "
                    "WHERE task_id = ?",
                    (now, task_id),
                )
                if task["provider_id"]:
                    self._conn.execute(
                        "UPDATE agents SET balance_cents = balance_cents + ? "
                        "WHERE id = ?",
                        (task["budget_cents"], task["provider_id"]),
                    )
            else:
                self._conn.execute(
                    "UPDATE payments SET status = 'refunded', settled_at = ? "
                    "WHERE task_id = ?",
                    (now, task_id),
                )
                self._conn.execute(
                    "UPDATE agents SET balance_cents = balance_cents + ? "
                    "WHERE id = ?",
                    (task["budget_cents"], task["requester_id"]),
                )
            self._conn.execute(
                "UPDATE tasks SET stage = 'settled', updated_at = ? WHERE task_id = ?",
                (now, task_id),
            )
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise
        return self.get_task(task_id)

    # ── Queries ───────────────────────────────────────────────────

    def list_tasks(self, limit: int = 20) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_stats(self) -> dict:
        row = self._conn.execute(
            "SELECT COUNT(*) as total_agents FROM agents WHERE active = 1"
        ).fetchone()
        total_agents = row["total_agents"]

        row = self._conn.execute(
            "SELECT COUNT(*) as total_tasks FROM tasks"
        ).fetchone()
        total_tasks = row["total_tasks"]

        row = self._conn.execute(
            "SELECT COALESCE(SUM(amount_cents), 0) as total_volume FROM payments "
            "WHERE status = 'released'"
        ).fetchone()
        total_volume = row["total_volume"]

        row = self._conn.execute(
            "SELECT COUNT(*) as active_tasks FROM tasks "
            "WHERE stage NOT IN ('settled')"
        ).fetchone()
        active_tasks = row["active_tasks"]

        return {
            "total_agents": total_agents,
            "total_tasks": total_tasks,
            "total_volume_cents": total_volume,
            "active_tasks": active_tasks,
        }
