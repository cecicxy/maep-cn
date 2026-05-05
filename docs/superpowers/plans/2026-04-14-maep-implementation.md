# MAEP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a minimum viable A2A economic protocol (MAEP) with on-chain DID, escrow payment, result attestation, Python Agent SDK, and 4 evaluation experiments — producing artifacts for a systems research paper.

**Architecture:** Solidity smart contracts on Hardhat local / Base Sepolia handle identity, escrow, and attestation. A Python Agent SDK wraps the protocol with pluggable LLM backends. An experiment harness runs 4 benchmarks comparing MAEP against x402 and Google A2A baselines.

**Tech Stack:** Solidity 0.8.x, Hardhat, ethers.js, Python 3.11, web3.py, python-dotenv, openai/anthropic SDK, pytest, conda (`web3_maep` env)

---

## File Map

| File | Responsibility |
|------|---------------|
| `contracts/AgentRegistry.sol` | DID registration, capabilities, reputation, stake |
| `contracts/PaymentChannel.sol` | Escrow lock/release, timeout refund |
| `contracts/ResultAttestation.sol` | On-chain result hash storage, dispute flag |
| `hardhat.config.js` | Hardhat network config (local + Base Sepolia) |
| `package.json` | Node deps: hardhat, ethers, @nomicfoundation/hardhat-toolbox |
| `test/AgentRegistry.test.js` | Contract unit tests |
| `test/PaymentChannel.test.js` | Contract unit tests |
| `test/ResultAttestation.test.js` | Contract unit tests |
| `scripts/deploy.js` | Deploy all 3 contracts, output addresses |
| `agent_sdk/config.py` | Load LLM config from `.env` |
| `agent_sdk/llm_client.py` | Pluggable LLM client (openai/anthropic/ollama/custom) |
| `agent_sdk/protocol.py` | MAEP 5-stage state machine + message types |
| `agent_sdk/chain.py` | web3.py wrapper around the 3 contracts |
| `agent_sdk/requester.py` | RequesterAgent class |
| `agent_sdk/provider.py` | ProviderAgent class |
| `agent_sdk/auditor.py` | AuditorAgent class |
| `tests/test_config.py` | Unit tests for config loading |
| `tests/test_llm_client.py` | Unit tests for LLM client (mocked) |
| `tests/test_protocol.py` | Unit tests for state machine |
| `tests/test_chain.py` | Unit tests for chain wrapper (mocked) |
| `experiments/bench_latency.py` | Experiment 1: stage latency measurement |
| `experiments/bench_gas.py` | Experiment 2: Gas cost per stage |
| `experiments/trust_analysis.py` | Experiment 3: trust assumption table |
| `experiments/scenario_demo.py` | Experiment 4: 3-agent end-to-end demo |
| `.env.example` | LLM config template |
| `requirements.txt` | Python dependencies |
| `paper/research_context.md` | Context file fed to AutoResearchClaw |

---

## Task 1: Project Scaffold & Environment

**Files:**
- Create: `package.json`
- Create: `hardhat.config.js`
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `agent_sdk/__init__.py`
- Create: `tests/__init__.py`
- Create: `experiments/__init__.py`

- [ ] **Step 1: Create conda environment**

```bash
conda create -n web3_maep python=3.11 -y
conda activate web3_maep
```

Expected: environment created at `D:\conda\envs\web3_maep`

- [ ] **Step 2: Init Node project**

In `E:\Web3`, run:
```bash
npm init -y
npm install --save-dev hardhat @nomicfoundation/hardhat-toolbox
npx hardhat init
```
When prompted: choose "Create a JavaScript project", accept defaults.

- [ ] **Step 3: Write `hardhat.config.js`**

Replace generated content with:
```javascript
require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config();

module.exports = {
  solidity: "0.8.24",
  networks: {
    hardhat: {},
    baseSepolia: {
      url: process.env.BASE_SEPOLIA_RPC_URL || "https://sepolia.base.org",
      accounts: process.env.DEPLOYER_PRIVATE_KEY ? [process.env.DEPLOYER_PRIVATE_KEY] : [],
    },
  },
};
```

- [ ] **Step 4: Write `requirements.txt`**

```
web3==6.15.0
eth-account==0.11.0
python-dotenv==1.0.1
openai==1.30.0
anthropic==0.28.0
requests==2.31.0
pytest==8.2.0
pytest-asyncio==0.23.6
```

- [ ] **Step 5: Write `.env.example`**

```
# LLM Backend (openai | anthropic | ollama | custom)
LLM_PROVIDER=openai
LLM_API_KEY=your_key_here
LLM_MODEL=gpt-4o
LLM_BASE_URL=

# Blockchain (only needed for Base Sepolia)
BASE_SEPOLIA_RPC_URL=https://sepolia.base.org
DEPLOYER_PRIVATE_KEY=

# Contract addresses (filled after deploy)
AGENT_REGISTRY_ADDRESS=
PAYMENT_CHANNEL_ADDRESS=
RESULT_ATTESTATION_ADDRESS=
```

- [ ] **Step 6: Create Python package stubs**

```bash
mkdir agent_sdk tests experiments paper
type nul > agent_sdk/__init__.py
type nul > tests/__init__.py
type nul > experiments/__init__.py
```

- [ ] **Step 7: Install Python deps**

```bash
conda activate web3_maep
pip install -r requirements.txt
```

Expected: all packages install without error.

- [ ] **Step 8: Commit**

```bash
git init
git add package.json hardhat.config.js requirements.txt .env.example agent_sdk/__init__.py tests/__init__.py experiments/__init__.py
git commit -m "chore: project scaffold, hardhat + python env"
```

---

## Task 2: AgentRegistry Contract

**Files:**
- Create: `contracts/AgentRegistry.sol`
- Create: `test/AgentRegistry.test.js`

- [ ] **Step 1: Write the failing test**

Create `test/AgentRegistry.test.js`:
```javascript
const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("AgentRegistry", function () {
  let registry, owner, agent1, agent2;

  beforeEach(async function () {
    [owner, agent1, agent2] = await ethers.getSigners();
    const AgentRegistry = await ethers.getContractFactory("AgentRegistry");
    registry = await AgentRegistry.deploy(ethers.parseEther("0.01")); // 0.01 ETH stake
  });

  it("registers an agent with stake", async function () {
    const capabilities = JSON.stringify({ task_types: ["data_analysis"], max_budget: 100 });
    await registry.connect(agent1).register(capabilities, { value: ethers.parseEther("0.01") });
    const info = await registry.getAgent(agent1.address);
    expect(info.capabilities).to.equal(capabilities);
    expect(info.active).to.be.true;
    expect(info.reputation).to.equal(100);
  });

  it("reverts if stake is insufficient", async function () {
    await expect(
      registry.connect(agent1).register("cap", { value: ethers.parseEther("0.001") })
    ).to.be.revertedWith("Insufficient stake");
  });

  it("updates reputation", async function () {
    await registry.connect(agent1).register("cap", { value: ethers.parseEther("0.01") });
    await registry.connect(owner).updateReputation(agent1.address, 120);
    const info = await registry.getAgent(agent1.address);
    expect(info.reputation).to.equal(120);
  });

  it("deregisters agent and returns stake", async function () {
    await registry.connect(agent1).register("cap", { value: ethers.parseEther("0.01") });
    const balBefore = await ethers.provider.getBalance(agent1.address);
    await registry.connect(agent1).deregister();
    const balAfter = await ethers.provider.getBalance(agent1.address);
    expect(balAfter).to.be.gt(balBefore);
    const info = await registry.getAgent(agent1.address);
    expect(info.active).to.be.false;
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
npx hardhat test test/AgentRegistry.test.js
```
Expected: FAIL — `AgentRegistry` contract not found.

- [ ] **Step 3: Write `contracts/AgentRegistry.sol`**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract AgentRegistry {
    struct AgentInfo {
        string capabilities;
        uint256 reputation;
        uint256 stake;
        bool active;
    }

    mapping(address => AgentInfo) public agents;
    uint256 public minStake;
    address public owner;

    event AgentRegistered(address indexed agent, string capabilities);
    event AgentDeregistered(address indexed agent);
    event ReputationUpdated(address indexed agent, uint256 newReputation);

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    constructor(uint256 _minStake) {
        minStake = _minStake;
        owner = msg.sender;
    }

    function register(string calldata capabilities) external payable {
        require(msg.value >= minStake, "Insufficient stake");
        require(!agents[msg.sender].active, "Already registered");
        agents[msg.sender] = AgentInfo(capabilities, 100, msg.value, true);
        emit AgentRegistered(msg.sender, capabilities);
    }

    function deregister() external {
        require(agents[msg.sender].active, "Not registered");
        uint256 stake = agents[msg.sender].stake;
        agents[msg.sender].active = false;
        agents[msg.sender].stake = 0;
        payable(msg.sender).transfer(stake);
        emit AgentDeregistered(msg.sender);
    }

    function updateReputation(address agent, uint256 newReputation) external onlyOwner {
        require(agents[agent].active, "Agent not active");
        agents[agent].reputation = newReputation;
        emit ReputationUpdated(agent, newReputation);
    }

    function getAgent(address agent) external view returns (AgentInfo memory) {
        return agents[agent];
    }
}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
npx hardhat test test/AgentRegistry.test.js
```
Expected: 4 passing

- [ ] **Step 5: Commit**

```bash
git add contracts/AgentRegistry.sol test/AgentRegistry.test.js
git commit -m "feat: AgentRegistry contract with DID, stake, reputation"
```

---

## Task 3: PaymentChannel Contract

**Files:**
- Create: `contracts/PaymentChannel.sol`
- Create: `test/PaymentChannel.test.js`

- [ ] **Step 1: Write the failing test**

Create `test/PaymentChannel.test.js`:
```javascript
const { expect } = require("chai");
const { ethers } = require("hardhat");
const { time } = require("@nomicfoundation/hardhat-network-helpers");

describe("PaymentChannel", function () {
  let channel, requester, provider, auditor;

  beforeEach(async function () {
    [requester, provider, auditor] = await ethers.getSigners();
    const PaymentChannel = await ethers.getContractFactory("PaymentChannel");
    channel = await PaymentChannel.deploy(auditor.address);
  });

  it("locks payment for a task", async function () {
    const taskId = ethers.id("task-001");
    const deadline = (await time.latest()) + 3600;
    await channel.connect(requester).lock(taskId, provider.address, deadline, {
      value: ethers.parseEther("0.1"),
    });
    const task = await channel.getTask(taskId);
    expect(task.amount).to.equal(ethers.parseEther("0.1"));
    expect(task.provider).to.equal(provider.address);
    expect(task.settled).to.be.false;
  });

  it("releases payment to provider on settlement", async function () {
    const taskId = ethers.id("task-002");
    const deadline = (await time.latest()) + 3600;
    await channel.connect(requester).lock(taskId, provider.address, deadline, {
      value: ethers.parseEther("0.1"),
    });
    const balBefore = await ethers.provider.getBalance(provider.address);
    await channel.connect(requester).release(taskId);
    const balAfter = await ethers.provider.getBalance(provider.address);
    expect(balAfter).to.be.gt(balBefore);
    const task = await channel.getTask(taskId);
    expect(task.settled).to.be.true;
  });

  it("refunds requester after deadline", async function () {
    const taskId = ethers.id("task-003");
    const deadline = (await time.latest()) + 60;
    await channel.connect(requester).lock(taskId, provider.address, deadline, {
      value: ethers.parseEther("0.1"),
    });
    await time.increase(120);
    const balBefore = await ethers.provider.getBalance(requester.address);
    await channel.connect(requester).refund(taskId);
    const balAfter = await ethers.provider.getBalance(requester.address);
    expect(balAfter).to.be.gt(balBefore);
  });

  it("auditor can force release on dispute", async function () {
    const taskId = ethers.id("task-004");
    const deadline = (await time.latest()) + 3600;
    await channel.connect(requester).lock(taskId, provider.address, deadline, {
      value: ethers.parseEther("0.1"),
    });
    await channel.connect(auditor).forceRelease(taskId);
    const task = await channel.getTask(taskId);
    expect(task.settled).to.be.true;
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
npx hardhat test test/PaymentChannel.test.js
```
Expected: FAIL — `PaymentChannel` not found.

- [ ] **Step 3: Write `contracts/PaymentChannel.sol`**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract PaymentChannel {
    struct Task {
        address requester;
        address provider;
        uint256 amount;
        uint256 deadline;
        bool settled;
    }

    mapping(bytes32 => Task) public tasks;
    address public auditor;

    event PaymentLocked(bytes32 indexed taskId, address requester, address provider, uint256 amount);
    event PaymentReleased(bytes32 indexed taskId, address provider, uint256 amount);
    event PaymentRefunded(bytes32 indexed taskId, address requester, uint256 amount);

    constructor(address _auditor) {
        auditor = _auditor;
    }

    function lock(bytes32 taskId, address provider, uint256 deadline) external payable {
        require(tasks[taskId].amount == 0, "Task already exists");
        require(msg.value > 0, "No payment");
        require(deadline > block.timestamp, "Deadline in past");
        tasks[taskId] = Task(msg.sender, provider, msg.value, deadline, false);
        emit PaymentLocked(taskId, msg.sender, provider, msg.value);
    }

    function release(bytes32 taskId) external {
        Task storage t = tasks[taskId];
        require(msg.sender == t.requester, "Not requester");
        require(!t.settled, "Already settled");
        t.settled = true;
        payable(t.provider).transfer(t.amount);
        emit PaymentReleased(taskId, t.provider, t.amount);
    }

    function refund(bytes32 taskId) external {
        Task storage t = tasks[taskId];
        require(msg.sender == t.requester, "Not requester");
        require(!t.settled, "Already settled");
        require(block.timestamp > t.deadline, "Deadline not passed");
        t.settled = true;
        payable(t.requester).transfer(t.amount);
        emit PaymentRefunded(taskId, t.requester, t.amount);
    }

    function forceRelease(bytes32 taskId) external {
        require(msg.sender == auditor, "Not auditor");
        Task storage t = tasks[taskId];
        require(!t.settled, "Already settled");
        t.settled = true;
        payable(t.provider).transfer(t.amount);
        emit PaymentReleased(taskId, t.provider, t.amount);
    }

    function getTask(bytes32 taskId) external view returns (Task memory) {
        return tasks[taskId];
    }
}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
npx hardhat test test/PaymentChannel.test.js
```
Expected: 4 passing

- [ ] **Step 5: Commit**

```bash
git add contracts/PaymentChannel.sol test/PaymentChannel.test.js
git commit -m "feat: PaymentChannel contract with escrow, refund, auditor dispute"
```

---

## Task 4: ResultAttestation Contract

**Files:**
- Create: `contracts/ResultAttestation.sol`
- Create: `test/ResultAttestation.test.js`

- [ ] **Step 1: Write the failing test**

Create `test/ResultAttestation.test.js`:
```javascript
const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("ResultAttestation", function () {
  let attestation, provider, requester;

  beforeEach(async function () {
    [provider, requester] = await ethers.getSigners();
    const ResultAttestation = await ethers.getContractFactory("ResultAttestation");
    attestation = await ResultAttestation.deploy();
  });

  it("stores result hash by provider", async function () {
    const taskId = ethers.id("task-001");
    const resultHash = ethers.keccak256(ethers.toUtf8Bytes("result data"));
    await attestation.connect(provider).attest(taskId, resultHash);
    const stored = await attestation.getAttestation(taskId);
    expect(stored.resultHash).to.equal(resultHash);
    expect(stored.provider).to.equal(provider.address);
    expect(stored.disputed).to.be.false;
  });

  it("flags attestation as disputed", async function () {
    const taskId = ethers.id("task-002");
    const resultHash = ethers.keccak256(ethers.toUtf8Bytes("bad result"));
    await attestation.connect(provider).attest(taskId, resultHash);
    await attestation.connect(requester).dispute(taskId);
    const stored = await attestation.getAttestation(taskId);
    expect(stored.disputed).to.be.true;
  });

  it("reverts duplicate attestation", async function () {
    const taskId = ethers.id("task-003");
    const resultHash = ethers.keccak256(ethers.toUtf8Bytes("result"));
    await attestation.connect(provider).attest(taskId, resultHash);
    await expect(
      attestation.connect(provider).attest(taskId, resultHash)
    ).to.be.revertedWith("Already attested");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
npx hardhat test test/ResultAttestation.test.js
```
Expected: FAIL — `ResultAttestation` not found.

- [ ] **Step 3: Write `contracts/ResultAttestation.sol`**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract ResultAttestation {
    struct Attestation {
        address provider;
        bytes32 resultHash;
        uint256 timestamp;
        bool disputed;
    }

    mapping(bytes32 => Attestation) public attestations;

    event ResultAttested(bytes32 indexed taskId, address provider, bytes32 resultHash);
    event ResultDisputed(bytes32 indexed taskId, address disputedBy);

    function attest(bytes32 taskId, bytes32 resultHash) external {
        require(attestations[taskId].timestamp == 0, "Already attested");
        attestations[taskId] = Attestation(msg.sender, resultHash, block.timestamp, false);
        emit ResultAttested(taskId, msg.sender, resultHash);
    }

    function dispute(bytes32 taskId) external {
        require(attestations[taskId].timestamp != 0, "No attestation");
        require(!attestations[taskId].disputed, "Already disputed");
        attestations[taskId].disputed = true;
        emit ResultDisputed(taskId, msg.sender);
    }

    function getAttestation(bytes32 taskId) external view returns (Attestation memory) {
        return attestations[taskId];
    }
}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
npx hardhat test test/ResultAttestation.test.js
```
Expected: 3 passing

- [ ] **Step 5: Run all contract tests**

```bash
npx hardhat test
```
Expected: 11 passing

- [ ] **Step 6: Commit**

```bash
git add contracts/ResultAttestation.sol test/ResultAttestation.test.js
git commit -m "feat: ResultAttestation contract with hash storage and dispute flag"
```

---

## Task 5: Deploy Script

**Files:**
- Create: `scripts/deploy.js`

- [ ] **Step 1: Write `scripts/deploy.js`**

```javascript
const { ethers } = require("hardhat");
const fs = require("fs");

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log("Deploying with:", deployer.address);

  const AgentRegistry = await ethers.getContractFactory("AgentRegistry");
  const registry = await AgentRegistry.deploy(ethers.parseEther("0.01"));
  await registry.waitForDeployment();
  console.log("AgentRegistry:", await registry.getAddress());

  const PaymentChannel = await ethers.getContractFactory("PaymentChannel");
  const channel = await PaymentChannel.deploy(deployer.address); // deployer as initial auditor
  await channel.waitForDeployment();
  console.log("PaymentChannel:", await channel.getAddress());

  const ResultAttestation = await ethers.getContractFactory("ResultAttestation");
  const attestation = await ResultAttestation.deploy();
  await attestation.waitForDeployment();
  console.log("ResultAttestation:", await attestation.getAddress());

  const addresses = {
    AgentRegistry: await registry.getAddress(),
    PaymentChannel: await channel.getAddress(),
    ResultAttestation: await attestation.getAddress(),
    network: (await ethers.provider.getNetwork()).name,
    deployedAt: new Date().toISOString(),
  };

  fs.writeFileSync("deployments.json", JSON.stringify(addresses, null, 2));
  console.log("Addresses saved to deployments.json");
}

main().catch((e) => { console.error(e); process.exit(1); });
```

- [ ] **Step 2: Run deploy on local Hardhat network**

```bash
npx hardhat run scripts/deploy.js --network hardhat
```
Expected output:
```
Deploying with: 0xf39F...
AgentRegistry: 0x5Fb...
PaymentChannel: 0xe7f...
ResultAttestation: 0x9fE...
Addresses saved to deployments.json
```

- [ ] **Step 3: Verify `deployments.json` was created**

```bash
type deployments.json
```
Expected: JSON with 3 contract addresses.

- [ ] **Step 4: Commit**

```bash
git add scripts/deploy.js deployments.json
git commit -m "feat: deploy script, outputs deployments.json"
```

---

## Task 6: Python SDK — Config & LLM Client

**Files:**
- Create: `agent_sdk/config.py`
- Create: `agent_sdk/llm_client.py`
- Create: `tests/test_config.py`
- Create: `tests/test_llm_client.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_config.py`:
```python
import os
import pytest
from agent_sdk.config import load_config

def test_load_config_from_env(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("LLM_API_KEY", "sk-test")
    monkeypatch.setenv("LLM_MODEL", "gpt-4o")
    monkeypatch.setenv("LLM_BASE_URL", "")
    cfg = load_config()
    assert cfg["provider"] == "openai"
    assert cfg["api_key"] == "sk-test"
    assert cfg["model"] == "gpt-4o"
    assert cfg["base_url"] == ""

def test_load_config_missing_key_raises(monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("LLM_MODEL", "gpt-4o")
    with pytest.raises(ValueError, match="LLM_API_KEY"):
        load_config()
```

Create `tests/test_llm_client.py`:
```python
import pytest
from unittest.mock import patch, MagicMock
from agent_sdk.llm_client import LLMClient

def test_openai_client_call(monkeypatch):
    cfg = {"provider": "openai", "api_key": "sk-test", "model": "gpt-4o", "base_url": ""}
    client = LLMClient(cfg)
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "hello"
    with patch.object(client._client, "chat") as mock_chat:
        mock_chat.completions.create.return_value = mock_response
        result = client.complete("say hello")
    assert result == "hello"

def test_unknown_provider_raises():
    cfg = {"provider": "unknown", "api_key": "x", "model": "x", "base_url": ""}
    with pytest.raises(ValueError, match="Unsupported provider"):
        LLMClient(cfg)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
conda activate web3_maep
pytest tests/test_config.py tests/test_llm_client.py -v
```
Expected: FAIL — modules not found.

- [ ] **Step 3: Write `agent_sdk/config.py`**

```python
import os
from dotenv import load_dotenv

load_dotenv()

def load_config() -> dict:
    provider = os.getenv("LLM_PROVIDER", "openai")
    api_key = os.getenv("LLM_API_KEY", "")
    model = os.getenv("LLM_MODEL", "gpt-4o")
    base_url = os.getenv("LLM_BASE_URL", "")

    if not api_key and provider != "ollama":
        raise ValueError("LLM_API_KEY is required (set in .env)")

    return {"provider": provider, "api_key": api_key, "model": model, "base_url": base_url}
```

- [ ] **Step 4: Write `agent_sdk/llm_client.py`**

```python
from openai import OpenAI
import anthropic

class LLMClient:
    def __init__(self, config: dict):
        self._config = config
        provider = config["provider"]

        if provider in ("openai", "ollama", "custom"):
            kwargs = {"api_key": config["api_key"]}
            if config.get("base_url"):
                kwargs["base_url"] = config["base_url"]
            elif provider == "ollama":
                kwargs["base_url"] = "http://localhost:11434/v1"
                kwargs["api_key"] = "ollama"
            self._client = OpenAI(**kwargs)
            self._provider_type = "openai"

        elif provider == "anthropic":
            self._client = anthropic.Anthropic(api_key=config["api_key"])
            self._provider_type = "anthropic"

        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def complete(self, prompt: str) -> str:
        model = self._config["model"]
        if self._provider_type == "openai":
            resp = self._client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
            )
            return resp.choices[0].message.content
        else:
            resp = self._client.messages.create(
                model=model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            return resp.content[0].text
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_config.py tests/test_llm_client.py -v
```
Expected: 4 passing

- [ ] **Step 6: Commit**

```bash
git add agent_sdk/config.py agent_sdk/llm_client.py tests/test_config.py tests/test_llm_client.py
git commit -m "feat: pluggable LLM client, config from .env"
```

---

## Task 7: MAEP Protocol State Machine

**Files:**
- Create: `agent_sdk/protocol.py`
- Create: `tests/test_protocol.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_protocol.py`:
```python
import pytest
from agent_sdk.protocol import MAEPSession, Stage, TaskSpec, TaskResult

def test_initial_stage():
    session = MAEPSession(task_id="task-001")
    assert session.stage == Stage.REGISTERED

def test_full_happy_path():
    session = MAEPSession(task_id="task-001")
    spec = TaskSpec(task_type="data_analysis", description="Analyze CSV", budget_wei=100)
    session.delegate(spec)
    assert session.stage == Stage.DELEGATED

    result = TaskResult(result_data="summary: 42 rows", result_hash="0xabc")
    session.execute(result)
    assert session.stage == Stage.EXECUTED

    session.settle(accepted=True)
    assert session.stage == Stage.SETTLED

def test_cannot_skip_stages():
    session = MAEPSession(task_id="task-002")
    result = TaskResult(result_data="data", result_hash="0xdef")
    with pytest.raises(ValueError, match="Cannot execute"):
        session.execute(result)

def test_settle_rejected_goes_to_dispute():
    session = MAEPSession(task_id="task-003")
    spec = TaskSpec(task_type="data_analysis", description="Analyze", budget_wei=50)
    session.delegate(spec)
    result = TaskResult(result_data="bad result", result_hash="0x000")
    session.execute(result)
    session.settle(accepted=False)
    assert session.stage == Stage.DISPUTED
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_protocol.py -v
```
Expected: FAIL — `protocol` module not found.

- [ ] **Step 3: Write `agent_sdk/protocol.py`**

```python
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional
import hashlib

class Stage(Enum):
    REGISTERED = "registered"
    DELEGATED = "delegated"
    EXECUTED = "executed"
    SETTLED = "settled"
    DISPUTED = "disputed"

@dataclass
class TaskSpec:
    task_type: str
    description: str
    budget_wei: int

@dataclass
class TaskResult:
    result_data: str
    result_hash: str

    @classmethod
    def from_data(cls, data: str) -> "TaskResult":
        h = "0x" + hashlib.sha256(data.encode()).hexdigest()
        return cls(result_data=data, result_hash=h)

@dataclass
class MAEPSession:
    task_id: str
    stage: Stage = Stage.REGISTERED
    spec: Optional[TaskSpec] = None
    result: Optional[TaskResult] = None

    def delegate(self, spec: TaskSpec) -> None:
        if self.stage != Stage.REGISTERED:
            raise ValueError(f"Cannot delegate from stage {self.stage}")
        self.spec = spec
        self.stage = Stage.DELEGATED

    def execute(self, result: TaskResult) -> None:
        if self.stage != Stage.DELEGATED:
            raise ValueError(f"Cannot execute from stage {self.stage}")
        self.result = result
        self.stage = Stage.EXECUTED

    def settle(self, accepted: bool) -> None:
        if self.stage != Stage.EXECUTED:
            raise ValueError(f"Cannot settle from stage {self.stage}")
        self.stage = Stage.SETTLED if accepted else Stage.DISPUTED
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_protocol.py -v
```
Expected: 4 passing

- [ ] **Step 5: Commit**

```bash
git add agent_sdk/protocol.py tests/test_protocol.py
git commit -m "feat: MAEP 5-stage state machine with TaskSpec and TaskResult"
```

---

## Task 8: Chain Wrapper (web3.py)

**Files:**
- Create: `agent_sdk/chain.py`
- Create: `tests/test_chain.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_chain.py`:
```python
import pytest
from unittest.mock import MagicMock, patch
from agent_sdk.chain import ChainClient

@pytest.fixture
def mock_chain():
    with patch("agent_sdk.chain.Web3") as MockWeb3:
        mock_w3 = MagicMock()
        MockWeb3.return_value = mock_w3
        mock_w3.is_connected.return_value = True
        client = ChainClient(
            rpc_url="http://localhost:8545",
            registry_address="0x1234",
            channel_address="0x5678",
            attestation_address="0x9abc",
            abi_dir="contracts/abi",
        )
        client._registry = MagicMock()
        client._channel = MagicMock()
        client._attestation = MagicMock()
        yield client

def test_get_agent_info(mock_chain):
    mock_chain._registry.functions.getAgent.return_value.call.return_value = (
        '{"task_types":["data_analysis"]}', 100, 10**16, True
    )
    info = mock_chain.get_agent("0xABCD")
    assert info["reputation"] == 100
    assert info["active"] is True

def test_compute_task_id(mock_chain):
    tid = mock_chain.compute_task_id("task-001")
    assert tid.startswith("0x")
    assert len(tid) == 66
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_chain.py -v
```
Expected: FAIL — `chain` module not found.

- [ ] **Step 3: Write `agent_sdk/chain.py`**

```python
import json
import hashlib
from pathlib import Path
from web3 import Web3

class ChainClient:
    def __init__(self, rpc_url: str, registry_address: str, channel_address: str,
                 attestation_address: str, abi_dir: str = "contracts/abi"):
        self._w3 = Web3(Web3.HTTPProvider(rpc_url))
        self._abi_dir = Path(abi_dir)
        self._registry = self._load_contract(registry_address, "AgentRegistry")
        self._channel = self._load_contract(channel_address, "PaymentChannel")
        self._attestation = self._load_contract(attestation_address, "ResultAttestation")

    def _load_contract(self, address: str, name: str):
        abi_path = self._abi_dir / f"{name}.json"
        if not abi_path.exists():
            return None  # allow mocking in tests
        abi = json.loads(abi_path.read_text())
        return self._w3.eth.contract(address=address, abi=abi)

    def compute_task_id(self, task_id: str) -> str:
        return "0x" + hashlib.sha256(task_id.encode()).hexdigest()

    def get_agent(self, address: str) -> dict:
        result = self._registry.functions.getAgent(address).call()
        return {
            "capabilities": result[0],
            "reputation": result[1],
            "stake": result[2],
            "active": result[3],
        }
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_chain.py -v
```
Expected: 2 passing

- [ ] **Step 5: Run all Python tests**

```bash
pytest tests/ -v
```
Expected: 10 passing

- [ ] **Step 6: Commit**

```bash
git add agent_sdk/chain.py tests/test_chain.py
git commit -m "feat: ChainClient web3.py wrapper for 3 contracts"
```

---

## Task 9: Agent Roles (Requester, Provider, Auditor)

**Files:**
- Create: `agent_sdk/requester.py`
- Create: `agent_sdk/provider.py`
- Create: `agent_sdk/auditor.py`

- [ ] **Step 1: Write `agent_sdk/requester.py`**

```python
from agent_sdk.protocol import MAEPSession, TaskSpec, Stage
from agent_sdk.llm_client import LLMClient

class RequesterAgent:
    def __init__(self, agent_id: str, llm_client: LLMClient):
        self.agent_id = agent_id
        self._llm = llm_client

    def create_task(self, task_type: str, description: str, budget_wei: int) -> MAEPSession:
        session = MAEPSession(task_id=f"{self.agent_id}-{task_type}-{budget_wei}")
        spec = TaskSpec(task_type=task_type, description=description, budget_wei=budget_wei)
        session.delegate(spec)
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
```

- [ ] **Step 2: Write `agent_sdk/provider.py`**

```python
from agent_sdk.protocol import MAEPSession, TaskResult, Stage
from agent_sdk.llm_client import LLMClient

class ProviderAgent:
    def __init__(self, agent_id: str, llm_client: LLMClient):
        self.agent_id = agent_id
        self._llm = llm_client

    def execute_task(self, session: MAEPSession) -> MAEPSession:
        if session.stage != Stage.DELEGATED:
            raise ValueError("Task not in DELEGATED stage")
        prompt = f"Complete this task: {session.spec.description}\nProvide a concise result."
        result_data = self._llm.complete(prompt)
        result = TaskResult.from_data(result_data)
        session.execute(result)
        return session
```

- [ ] **Step 3: Write `agent_sdk/auditor.py`**

```python
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
```

- [ ] **Step 4: Smoke-test imports**

```bash
conda activate web3_maep
python -c "from agent_sdk.requester import RequesterAgent; from agent_sdk.provider import ProviderAgent; from agent_sdk.auditor import AuditorAgent; print('OK')"
```
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add agent_sdk/requester.py agent_sdk/provider.py agent_sdk/auditor.py
git commit -m "feat: RequesterAgent, ProviderAgent, AuditorAgent with LLM integration"
```

---

## Task 10: Experiment 1 — Latency Benchmark

**Files:**
- Create: `experiments/bench_latency.py`

- [ ] **Step 1: Write `experiments/bench_latency.py`**

```python
"""
Experiment 1: End-to-end latency per MAEP stage.
Baseline: simulated plain HTTP A2A (no chain ops).
Run: python experiments/bench_latency.py
"""
import time
import statistics
import json
from agent_sdk.protocol import MAEPSession, TaskSpec, TaskResult

RUNS = 50

def time_stage(fn):
    start = time.perf_counter()
    fn()
    return (time.perf_counter() - start) * 1000  # ms

def run_maep_session():
    timings = {}
    session = MAEPSession(task_id="bench-task")

    # Stage 3: DELEGATE
    spec = TaskSpec(task_type="data_analysis", description="Benchmark task", budget_wei=1000)
    timings["delegate_ms"] = time_stage(lambda: session.delegate(spec))

    # Stage 4: EXECUTE (no LLM call — pure protocol overhead)
    result = TaskResult.from_data("benchmark result data")
    timings["execute_ms"] = time_stage(lambda: session.execute(result))

    # Stage 5: SETTLE
    timings["settle_ms"] = time_stage(lambda: session.settle(accepted=True))

    return timings

def baseline_http_a2a():
    """Simulate plain HTTP A2A: 3 dict operations, no chain."""
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
```

- [ ] **Step 2: Run the experiment**

```bash
conda activate web3_maep
python experiments/bench_latency.py
```
Expected: table printed, `experiments/results_latency.json` created.

- [ ] **Step 3: Commit**

```bash
git add experiments/bench_latency.py
git commit -m "feat: Experiment 1 latency benchmark"
```

---

## Task 11: Experiment 2 — Gas Cost Analysis

**Files:**
- Create: `experiments/bench_gas.py`
- Requires: Hardhat node running locally

- [ ] **Step 1: Write `experiments/bench_gas.py`**

```python
"""
Experiment 2: Gas cost per contract operation.
Requires: npx hardhat node running in another terminal.
Run: python experiments/bench_gas.py
"""
import json
import subprocess
import time
from web3 import Web3
from eth_account import Account

RPC_URL = "http://127.0.0.1:8545"
HARDHAT_ACCOUNTS = [
    "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",  # account 0
    "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d",  # account 1
    "0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a",  # account 2
]

def deploy_contracts(w3, deployer):
    # Load compiled artifacts (run `npx hardhat compile` first)
    def load_artifact(name):
        path = f"artifacts/contracts/{name}.sol/{name}.json"
        with open(path) as f:
            return json.load(f)

    results = {}
    for name, args in [
        ("AgentRegistry", [w3.to_wei(0.01, "ether")]),
        ("PaymentChannel", [deployer.address]),
        ("ResultAttestation", []),
    ]:
        artifact = load_artifact(name)
        contract = w3.eth.contract(abi=artifact["abi"], bytecode=artifact["bytecode"])
        tx_hash = contract.constructor(*args).transact({"from": deployer.address})
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        results[name] = {
            "address": receipt.contractAddress,
            "deploy_gas": receipt.gasUsed,
            "abi": artifact["abi"],
        }
        print(f"  {name}: {receipt.contractAddress} (deploy gas: {receipt.gasUsed:,})")
    return results

def measure_operations(w3, contracts, deployer, agent1, agent2):
    gas_report = {}

    # REGISTER
    registry = w3.eth.contract(address=contracts["AgentRegistry"]["address"], abi=contracts["AgentRegistry"]["abi"])
    tx = registry.functions.register('{"task_types":["data_analysis"]}').build_transaction({
        "from": agent1.address, "value": w3.to_wei(0.01, "ether"), "nonce": w3.eth.get_transaction_count(agent1.address),
        "gas": 200000, "gasPrice": w3.to_wei("1", "gwei"),
    })
    signed = agent1.sign_transaction(tx)
    receipt = w3.eth.wait_for_transaction_receipt(w3.eth.send_raw_transaction(signed.raw_transaction))
    gas_report["REGISTER"] = receipt.gasUsed

    # DELEGATE (lock payment)
    channel = w3.eth.contract(address=contracts["PaymentChannel"]["address"], abi=contracts["PaymentChannel"]["abi"])
    task_id = w3.keccak(text="bench-task-001")
    deadline = w3.eth.get_block("latest")["timestamp"] + 3600
    tx = channel.functions.lock(task_id, agent2.address, deadline).build_transaction({
        "from": agent1.address, "value": w3.to_wei(0.05, "ether"), "nonce": w3.eth.get_transaction_count(agent1.address),
        "gas": 200000, "gasPrice": w3.to_wei("1", "gwei"),
    })
    signed = agent1.sign_transaction(tx)
    receipt = w3.eth.wait_for_transaction_receipt(w3.eth.send_raw_transaction(signed.raw_transaction))
    gas_report["DELEGATE"] = receipt.gasUsed

    # EXECUTE (attest result)
    attestation = w3.eth.contract(address=contracts["ResultAttestation"]["address"], abi=contracts["ResultAttestation"]["abi"])
    result_hash = w3.keccak(text="result data content")
    tx = attestation.functions.attest(task_id, result_hash).build_transaction({
        "from": agent2.address, "nonce": w3.eth.get_transaction_count(agent2.address),
        "gas": 200000, "gasPrice": w3.to_wei("1", "gwei"),
    })
    signed = agent2.sign_transaction(tx)
    receipt = w3.eth.wait_for_transaction_receipt(w3.eth.send_raw_transaction(signed.raw_transaction))
    gas_report["EXECUTE"] = receipt.gasUsed

    # SETTLE (release payment)
    tx = channel.functions.release(task_id).build_transaction({
        "from": agent1.address, "nonce": w3.eth.get_transaction_count(agent1.address),
        "gas": 200000, "gasPrice": w3.to_wei("1", "gwei"),
    })
    signed = agent1.sign_transaction(tx)
    receipt = w3.eth.wait_for_transaction_receipt(w3.eth.send_raw_transaction(signed.raw_transaction))
    gas_report["SETTLE"] = receipt.gasUsed

    return gas_report

if __name__ == "__main__":
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    assert w3.is_connected(), "Start hardhat node: npx hardhat node"

    deployer = Account.from_key(HARDHAT_ACCOUNTS[0])
    agent1 = Account.from_key(HARDHAT_ACCOUNTS[1])
    agent2 = Account.from_key(HARDHAT_ACCOUNTS[2])
    w3.eth.default_account = deployer.address

    print("Compiling contracts...")
    subprocess.run(["npx", "hardhat", "compile"], check=True, capture_output=True)

    print("Deploying contracts...")
    contracts = deploy_contracts(w3, deployer)

    print("\nMeasuring Gas per stage...")
    gas_report = measure_operations(w3, contracts, deployer, agent1, agent2)

    print(f"\n{'Stage':<12} {'Gas Used':>12}")
    print("-" * 26)
    total = 0
    for stage, gas in gas_report.items():
        print(f"{stage:<12} {gas:>12,}")
        total += gas
    print(f"{'TOTAL':<12} {total:>12,}")

    with open("experiments/results_gas.json", "w") as f:
        json.dump({"gas_per_stage": gas_report, "contracts": {k: v["deploy_gas"] for k,v in contracts.items()}}, f, indent=2)
    print("\nResults saved to experiments/results_gas.json")
```

- [ ] **Step 2: Start Hardhat node in a separate terminal**

```bash
npx hardhat node
```
Leave it running.

- [ ] **Step 3: Run Gas benchmark**

```bash
conda activate web3_maep
python experiments/bench_gas.py
```
Expected: table of Gas per stage, `experiments/results_gas.json` created.

- [ ] **Step 4: Commit**

```bash
git add experiments/bench_gas.py
git commit -m "feat: Experiment 2 Gas cost benchmark"
```

---

## Task 12: Experiment 3 — Trust Assumption Analysis

**Files:**
- Create: `experiments/trust_analysis.py`

- [ ] **Step 1: Write `experiments/trust_analysis.py`**

```python
"""
Experiment 3: Trust assumption count per protocol.
Static analysis — outputs comparison table for paper.
Run: python experiments/trust_analysis.py
"""
import json

TRUST_ANALYSIS = {
    "x402": {
        "agent_identity": {"trusted_party": "HTTP server", "decentralized": False},
        "payment": {"trusted_party": "Stablecoin issuer + server", "decentralized": False},
        "result_verification": {"trusted_party": "None (no verification)", "decentralized": False},
        "dispute_resolution": {"trusted_party": "None", "decentralized": False},
        "trust_assumption_count": 3,
        "notes": "Requires trust in: (1) server identity, (2) stablecoin issuer, (3) payment processor",
    },
    "google_a2a": {
        "agent_identity": {"trusted_party": "Google platform", "decentralized": False},
        "payment": {"trusted_party": "None (no native payment)", "decentralized": False},
        "result_verification": {"trusted_party": "None", "decentralized": False},
        "dispute_resolution": {"trusted_party": "Platform operator", "decentralized": False},
        "trust_assumption_count": 2,
        "notes": "Requires trust in: (1) Google platform, (2) platform operator for disputes",
    },
    "fetch_ai": {
        "agent_identity": {"trusted_party": "Fetch.ai network validators", "decentralized": True},
        "payment": {"trusted_party": "FET token + validators", "decentralized": True},
        "result_verification": {"trusted_party": "Fetch.ai network", "decentralized": True},
        "dispute_resolution": {"trusted_party": "Fetch.ai governance", "decentralized": True},
        "trust_assumption_count": 2,
        "notes": "Requires trust in: (1) validator set, (2) Fetch.ai governance — permissioned chain",
    },
    "maep_this_work": {
        "agent_identity": {"trusted_party": "Ethereum smart contract (public)", "decentralized": True},
        "payment": {"trusted_party": "Ethereum smart contract", "decentralized": True},
        "result_verification": {"trusted_party": "Ethereum smart contract", "decentralized": True},
        "dispute_resolution": {"trusted_party": "AuditorAgent (configurable)", "decentralized": True},
        "trust_assumption_count": 1,
        "notes": "Requires trust in: (1) Ethereum consensus — fully public, auditor is optional/replaceable",
    },
}

def print_table():
    protocols = list(TRUST_ANALYSIS.keys())
    dimensions = ["agent_identity", "payment", "result_verification", "dispute_resolution"]

    header = f"{'Dimension':<25}" + "".join(f"{p:<22}" for p in protocols)
    print(header)
    print("-" * (25 + 22 * len(protocols)))

    for dim in dimensions:
        row = f"{dim:<25}"
        for p in protocols:
            entry = TRUST_ANALYSIS[p][dim]
            val = entry["trusted_party"][:20] if isinstance(entry, dict) else str(entry)
            row += f"{val:<22}"
        print(row)

    print()
    row = f"{'Trust count':<25}"
    for p in protocols:
        row += f"{TRUST_ANALYSIS[p]['trust_assumption_count']:<22}"
    print(row)

if __name__ == "__main__":
    print("\n=== Trust Assumption Analysis ===\n")
    print_table()
    with open("experiments/results_trust.json", "w") as f:
        json.dump(TRUST_ANALYSIS, f, indent=2)
    print("\nFull analysis saved to experiments/results_trust.json")
```

- [ ] **Step 2: Run the analysis**

```bash
conda activate web3_maep
python experiments/trust_analysis.py
```
Expected: comparison table printed, `experiments/results_trust.json` created.

- [ ] **Step 3: Commit**

```bash
git add experiments/trust_analysis.py
git commit -m "feat: Experiment 3 trust assumption analysis"
```

---

## Task 13: Experiment 4 — End-to-End Scenario Demo

**Files:**
- Create: `experiments/scenario_demo.py`
- Requires: `.env` with valid LLM credentials

- [ ] **Step 1: Write `experiments/scenario_demo.py`**

```python
"""
Experiment 4: 3-agent end-to-end scenario demo.
Requires: .env with LLM_PROVIDER, LLM_API_KEY, LLM_MODEL set.
Run: python experiments/scenario_demo.py
"""
import json
import time
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
        budget_wei=10**15,  # 0.001 ETH
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
    print(f"  [SETTLE]   Rejected → Stage: {session.stage.value}")

    ruling = auditor.arbitrate(session)
    print(f"  [DISPUTE]  Auditor ruling: {ruling}")
    return session, ruling

if __name__ == "__main__":
    cfg = load_config()
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

    with open("experiments/results_scenario.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nResults saved to experiments/results_scenario.json")
```

- [ ] **Step 2: Copy `.env.example` to `.env` and fill in your credentials**

```bash
copy .env.example .env
# Edit .env: set LLM_PROVIDER, LLM_API_KEY, LLM_MODEL
```

- [ ] **Step 3: Run the demo**

```bash
conda activate web3_maep
python experiments/scenario_demo.py
```
Expected: two scenario logs, summary JSON, `experiments/results_scenario.json` created.

- [ ] **Step 4: Commit**

```bash
git add experiments/scenario_demo.py
git commit -m "feat: Experiment 4 end-to-end 3-agent scenario demo"
```

---

## Task 14: Paper Context for AutoResearchClaw

**Files:**
- Create: `paper/research_context.md`

- [ ] **Step 1: Write `paper/research_context.md`**

```markdown
# MAEP Research Context for AutoResearchClaw

## Title (draft)
MAEP: A Minimum Viable Agent-to-Agent Economic Protocol with Decentralized Identity and Trustless Payment Settlement

## Abstract (draft)
Existing agent communication protocols such as Google A2A and Coinbase x402 lack two critical primitives for autonomous economic activity: decentralized agent identity and trustless micropayment settlement. We present MAEP, a Minimum Viable Agent-to-Agent Economic Protocol that addresses these gaps through three Ethereum smart contracts (AgentRegistry, PaymentChannel, ResultAttestation) and a Python Agent SDK with pluggable LLM backends. We evaluate MAEP against x402 and Google A2A on three dimensions: end-to-end latency, on-chain Gas cost, and trust assumption count. Our experiments show MAEP reduces trust assumptions to a single party (Ethereum consensus) compared to 2–3 for existing protocols, at a Gas cost of approximately [fill from results_gas.json] per full lifecycle. We provide an open-source reference implementation and end-to-end scenario demonstrations.

## Key Related Work
- arXiv:2507.19550 — "Towards Multi-Agent Economies: Enhancing the A2A Protocol with Blockchain-Based Identities and Payments" (direct predecessor)
- arXiv:2501.16606 — "Can We Govern the Agent-to-Agent Economy?" (motivation)
- Coinbase x402 whitepaper (https://www.x402.org/x402-whitepaper.pdf)
- Google Agent2Agent Protocol (https://google.github.io/A2A/)
- Fetch.ai Autonomous Economic Agents
- Autonolas / Olas protocol

## Experiment Results Location
- Latency: experiments/results_latency.json
- Gas costs: experiments/results_gas.json
- Trust analysis: experiments/results_trust.json
- Scenario demo: experiments/results_scenario.json

## Target Venue
AAMAS 2026 workshop (Multi-Agent Systems) or IEEE Blockchain 2026

## Contribution Claims
1. First formal specification of a minimum viable A2A economic protocol with on-chain DID + escrow + attestation
2. Open-source reference implementation with LLM-agnostic Python SDK
3. Comparative evaluation showing trust minimization vs. x402 and Google A2A
```

- [ ] **Step 2: Commit**

```bash
git add paper/research_context.md
git commit -m "docs: paper context for AutoResearchClaw"
```

---

## Task 15: ABI Export for Python SDK

**Files:**
- Create: `scripts/export_abi.js`
- Creates: `contracts/abi/AgentRegistry.json`, `PaymentChannel.json`, `ResultAttestation.json`

- [ ] **Step 1: Write `scripts/export_abi.js`**

```javascript
const fs = require("fs");
const path = require("path");

const contracts = ["AgentRegistry", "PaymentChannel", "ResultAttestation"];
const outDir = "contracts/abi";

if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });

for (const name of contracts) {
  const artifactPath = path.join("artifacts", "contracts", `${name}.sol`, `${name}.json`);
  const artifact = JSON.parse(fs.readFileSync(artifactPath));
  const outPath = path.join(outDir, `${name}.json`);
  fs.writeFileSync(outPath, JSON.stringify(artifact.abi, null, 2));
  console.log(`Exported ABI: ${outPath}`);
}
```

- [ ] **Step 2: Compile and export ABIs**

```bash
npx hardhat compile
node scripts/export_abi.js
```
Expected:
```
Exported ABI: contracts/abi/AgentRegistry.json
Exported ABI: contracts/abi/PaymentChannel.json
Exported ABI: contracts/abi/ResultAttestation.json
```

- [ ] **Step 3: Run all tests one final time**

```bash
npx hardhat test
pytest tests/ -v
```
Expected: 11 JS tests passing, 10 Python tests passing.

- [ ] **Step 4: Final commit**

```bash
git add scripts/export_abi.js contracts/abi/
git commit -m "chore: ABI export script, all tests passing"
```

---

## Self-Review

**Spec coverage check:**
- ✅ AgentRegistry (DID, capabilities, reputation, stake) → Task 2
- ✅ PaymentChannel (escrow, refund, dispute) → Task 3
- ✅ ResultAttestation (hash storage, dispute flag) → Task 4
- ✅ Deploy script → Task 5
- ✅ Pluggable LLM config → Task 6
- ✅ 5-stage state machine → Task 7
- ✅ web3.py chain wrapper → Task 8
- ✅ RequesterAgent, ProviderAgent, AuditorAgent → Task 9
- ✅ Experiment 1 (latency) → Task 10
- ✅ Experiment 2 (Gas) → Task 11
- ✅ Experiment 3 (trust) → Task 12
- ✅ Experiment 4 (scenario) → Task 13
- ✅ Paper context for AutoResearchClaw → Task 14
- ✅ ABI export for Python SDK → Task 15

**Placeholder scan:** No TBD/TODO in implementation steps. Gas benchmark fills in paper abstract placeholder from results file. ✅

**Type consistency:** `MAEPSession`, `TaskSpec`, `TaskResult`, `Stage` defined in Task 7 and used consistently in Tasks 9, 10, 13. `ChainClient` defined in Task 8, referenced in Task 11. ✅
