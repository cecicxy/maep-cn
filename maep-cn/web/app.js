const API = window.location.origin + "/api";

// ── Stats Dashboard ──────────────────────────────────────────────
async function fetchStats() {
    try {
        const res = await fetch(`${API}/stats`);
        if (!res.ok) throw new Error("API unavailable");
        const data = await res.json();
        animateCountUp("statAgents", data.total_agents);
        animateCountUp("statTasks", data.total_tasks);
        animateCountUp("statVolume", data.total_volume_cents);
        animateCountUp("statActive", data.active_tasks);
    } catch {
        document.querySelectorAll(".stat-value").forEach(el => {
            if (el.textContent === "--") el.textContent = "N/A";
        });
    }
}

function animateCountUp(id, target) {
    const el = document.getElementById(id);
    if (!el) return;
    const start = parseInt(el.textContent) || 0;
    const diff = target - start;
    if (diff === 0) { el.textContent = target; return; }
    const duration = 600;
    const startTime = performance.now();

    function tick(now) {
        const t = Math.min((now - startTime) / duration, 1);
        const eased = 1 - Math.pow(1 - t, 3);
        el.textContent = Math.round(start + diff * eased);
        if (t < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
}

// ── Demo Helpers ─────────────────────────────────────────────────
function log(msg, cls = "") {
    const logEl = document.getElementById("demoLog");
    if (!logEl) return;
    const placeholder = logEl.querySelector(".log-placeholder");
    if (placeholder) placeholder.remove();

    const time = new Date().toLocaleTimeString();
    const entry = document.createElement("div");
    entry.className = "log-entry";
    entry.innerHTML = `<span class="log-time">[${time}]</span> <span class="${cls}">${msg}</span>`;
    logEl.appendChild(entry);
    logEl.scrollTop = logEl.scrollHeight;
}

function clearDemoLog() {
    const logEl = document.getElementById("demoLog");
    if (!logEl) return;
    logEl.innerHTML = '<div class="log-placeholder" style="color:#ffffff;">点击上方按钮开始演示...</div>';
}

async function api(method, path, body) {
    const opts = { method, headers: { "Content-Type": "application/json" } };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(`${API}${path}`, opts);
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || JSON.stringify(data));
    return data;
}

function formatCents(cents) {
    return `RMB ${(cents / 100).toFixed(2)}`;
}

// ── Happy Path Demo ──────────────────────────────────────────────
async function runHappyPath() {
    const prefix = "happy-" + Date.now();
    try {
        log("=== Happy Path Demo ===", "log-stage");

        log("Register Requester (deposit RMB 100)...");
        const req = await api("POST", "/agents", {
            id: `${prefix}-requester`, name: "Requester",
            capabilities: "translation", initial_deposit_cents: 10000,
        });
        log(`Requester balance: ${formatCents(req.balance_cents)}`, "log-balance");

        log("Register Provider (deposit RMB 100)...");
        const prov = await api("POST", "/agents", {
            id: `${prefix}-provider`, name: "Provider",
            capabilities: "translation", initial_deposit_cents: 10000,
        });
        log(`Provider balance: ${formatCents(prov.balance_cents)}`, "log-balance");

        log("Create task (budget RMB 5, locked from Requester balance)...");
        const task = await api("POST", "/tasks", {
            requester_id: `${prefix}-requester`,
            task_type: "translation", description: "Translate to English: hello world",
            budget_cents: 500,
        });
        log(`Task created: ${task.task_id}`, "log-stage");
        const reqBal = (await api("GET", `/agents/${prefix}-requester`)).balance_cents;
        log(`Requester balance: ${formatCents(reqBal)}`, "log-balance");

        log("Provider executes task, submitting result...");
        const exec = await api("POST", `/tasks/${task.task_id}/execute`, {
            provider_id: `${prefix}-provider`,
            result_data: "Hello World",
        });
        log(`Executed: result_hash=${exec.result_hash?.slice(0, 18)}...`, "log-stage");

        log("Requester verifies result -> accept");
        const settle = await api("POST", `/tasks/${task.task_id}/verify`, { accepted: true });
        log(settle.message, "log-stage");

        const reqFinal = await api("GET", `/agents/${prefix}-requester`);
        const provFinal = await api("GET", `/agents/${prefix}-provider`);
        log(`Requester balance: ${formatCents(reqFinal.balance_cents)}`, "log-balance");
        log(`Provider balance: ${formatCents(provFinal.balance_cents)}`, "log-balance");
        log("=== Happy Path Complete ===", "log-stage");

        fetchStats();
    } catch (e) {
        log(`Error: ${e.message}`, "log-error");
    }
}

// ── Dispute Path Demo ────────────────────────────────────────────
async function runDisputePath() {
    const prefix = "disp-" + Date.now();
    try {
        log("=== Dispute Path Demo ===", "log-stage");

        log("Register 3 Agents...");
        await api("POST", "/agents", {
            id: `${prefix}-requester`, name: "Requester",
            capabilities: "analysis", initial_deposit_cents: 10000,
        });
        await api("POST", "/agents", {
            id: `${prefix}-provider`, name: "Provider",
            capabilities: "analysis", initial_deposit_cents: 10000,
        });
        await api("POST", "/agents", {
            id: `${prefix}-auditor`, name: "Auditor",
            capabilities: "audit", initial_deposit_cents: 10000,
        });

        log("Create task (budget RMB 3)...");
        const task = await api("POST", "/tasks", {
            requester_id: `${prefix}-requester`,
            task_type: "analysis", description: "Analyze data trends",
            budget_cents: 300,
        });

        log("Provider executes and submits result...");
        await api("POST", `/tasks/${task.task_id}/execute`, {
            provider_id: `${prefix}-provider`,
            result_data: "Data shows downward trend",
        });

        log("Requester rejects result -> dispute");
        await api("POST", `/tasks/${task.task_id}/verify`, { accepted: false });
        log("Task enters disputed state", "log-stage");

        log("Filing dispute...");
        await api("POST", `/tasks/${task.task_id}/dispute`, { disputed_by: `${prefix}-requester` });

        log("Auditor arbitrates...");
        await api("POST", `/tasks/${task.task_id}/arbitrate`, { auditor_id: `${prefix}-auditor` });
        log("Arbitration complete, task settled", "log-stage");

        const reqFinal = await api("GET", `/agents/${prefix}-requester`);
        const provFinal = await api("GET", `/agents/${prefix}-provider`);
        log(`Requester balance: ${formatCents(reqFinal.balance_cents)}`, "log-balance");
        log(`Provider balance: ${formatCents(provFinal.balance_cents)}`, "log-balance");
        log("=== Dispute Path Complete ===", "log-stage");

        fetchStats();
    } catch (e) {
        log(`Error: ${e.message}`, "log-error");
    }
}

// ── Code Tab Switching ───────────────────────────────────────────
function showCodeTab(index) {
    document.querySelectorAll(".code-tab").forEach((tab, i) => {
        tab.classList.toggle("active", i === index);
    });
    document.querySelectorAll(".code-panel").forEach((panel, i) => {
        panel.classList.toggle("active", i === index);
    });
}

// ── Flow Animation (index page only) ─────────────────────────────
function animateFlow() {
    const steps = document.querySelectorAll(".flow-step");
    if (steps.length === 0) return;
    let i = 0;
    const interval = setInterval(() => {
        steps.forEach(s => s.classList.remove("active"));
        if (i < steps.length) {
            steps[i].classList.add("active");
            i++;
        } else {
            i = 0;
        }
    }, 1200);
    setTimeout(() => clearInterval(interval), 20000);
}

// ── Init ─────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
    fetchStats();
    animateFlow();
    setInterval(fetchStats, 5000);
});
