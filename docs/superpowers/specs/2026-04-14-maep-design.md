# MAEP: Minimum Viable Agent-to-Agent Economic Protocol
**Design Spec — 2026-04-14**

## 1. Research Positioning

### Problem
Existing A2A protocols (Google A2A, Coinbase x402) lack two critical modules:
1. **Decentralized Agent Identity** — agents rely on centralized platform trust
2. **Native Micropayment Settlement** — no trustless escrow or result verification

### Core Contributions
1. **Protocol Specification**: Formal definition of MAEP's 5-stage interaction flow (Register → Discover → Delegate → Execute → Settle)
2. **Reference Implementation**: Solidity smart contracts + Python Agent SDK with pluggable LLM backend (user-configurable API key via `.env`)
3. **Evaluation**: Comparison with x402 and Google A2A on latency, Gas cost, and trust assumption count

### Target Venue
AAMAS 2026 workshop or IEEE Blockchain 2026 (experimental systems paper)

---

## 2. System Architecture

### Five-Layer Stack
```
Layer 5: AutoResearchClaw         — paper generation
Layer 4: Experiment Harness       — latency / gas / baseline comparison
Layer 3: Python Agent SDK         — AgentClient, pluggable LLM, .env config
Layer 2: MAEP Protocol Engine     — 5-stage state machine, message format, validation
Layer 1: Smart Contracts          — AgentRegistry, PaymentChannel, ResultAttestation
                ↕
         Hardhat local / Base Sepolia testnet
```

### Smart Contracts
- `AgentRegistry.sol`: DID registration, capability declaration, reputation score
- `PaymentChannel.sol`: Lock tokens on task delegation, release on verified result
- `ResultAttestation.sol`: Store result hash on-chain for dispute resolution

### Python SDK
- `config.py`: Reads `LLM_PROVIDER`, `LLM_API_KEY`, `LLM_MODEL` from `.env`
- Supported providers: `openai`, `anthropic`, `ollama`, any OpenAI-compatible endpoint
- Agent roles: `RequesterAgent`, `ProviderAgent`, `AuditorAgent`

### Directory Structure
```
E:\Web3\
├── contracts/
│   ├── AgentRegistry.sol
│   ├── PaymentChannel.sol
│   └── ResultAttestation.sol
├── agent_sdk/
│   ├── config.py
│   ├── requester.py
│   ├── provider.py
│   └── auditor.py
├── experiments/
│   ├── bench_latency.py
│   ├── bench_gas.py
│   ├── trust_analysis.py
│   └── scenario_demo.py
├── paper/                  # AutoResearchClaw output
├── hardhat.config.js
├── package.json
├── .env.example
└── requirements.txt
```

---

## 3. MAEP Protocol: 5-Stage Flow

### Stage Definitions

| Stage | Actor | On-chain? | Key Action |
|-------|-------|-----------|------------|
| 1. REGISTER | Both | Yes | Submit DID + capabilities + stake |
| 2. DISCOVER | Requester | No (off-chain) | Match by task_type + budget |
| 3. DELEGATE | Requester | Yes | Lock payment in escrow, send task spec |
| 4. EXECUTE | Provider | Yes | Submit `keccak256(result)` + proof |
| 5. SETTLE | Both | Yes | Verify result, release payment, update reputation |

### Key Design Decisions
- **REGISTER**: Capability description as JSON Schema; small token stake to prevent Sybil attacks
- **DISCOVER**: Off-chain Python matching to minimize Gas; on-chain registry as source of truth
- **DELEGATE**: `PaymentChannel.lock(taskId, amount, deadline)` — auto-refund on timeout
- **EXECUTE**: Provider submits `keccak256(result)` on-chain before revealing full result
- **SETTLE**: Requester verifies; dispute escalates to `AuditorAgent`

### Comparison with Existing Protocols

| Dimension | x402 | Google A2A | MAEP (this work) |
|-----------|------|------------|------------------|
| Agent Identity | None | Centralized | On-chain DID |
| Payment | HTTP + USDC | None | Smart contract escrow |
| Result Verification | None | None | On-chain hash attestation |
| Trust Assumptions | Server | Platform | Minimized (contract) |

---

## 4. Evaluation Plan

### Experiment 1: Latency Overhead
- Measure end-to-end latency across all 5 MAEP stages
- Baselines: plain HTTP A2A, x402
- Environments: Hardhat local (controlled) + Base Sepolia (realistic)
- Expected finding: on-chain operations add latency but eliminate third-party trust

### Experiment 2: Gas Cost Analysis
- Per-stage Gas consumption: REGISTER / DELEGATE / SETTLE / DISPUTE
- Before/after optimization comparison (e.g., off-chain DISCOVER savings)
- Purpose: justify each design decision quantitatively

### Experiment 3: Trust Assumption Minimization
- Formally enumerate trust assumptions per protocol
- Compare: MAEP vs x402 vs Google A2A vs Fetch.ai
- Output: table for paper's theoretical contribution section

### Experiment 4: End-to-End Scenario Demo (qualitative)
- 3-agent task: data analysis delegation
  - `RequesterAgent` issues task (any LLM backend)
  - `ProviderAgent` executes and submits result
  - `AuditorAgent` handles simulated dispute
- Logs and screenshots as paper figures

---

## 5. Environment & Dependencies

### Conda Environment
- New environment: `web3_maep` (created when needed)
- Special packages: `web3`, `eth-account`, `hardhat` (via npm), `openai`, `anthropic`, `python-dotenv`

### LLM Configuration (`.env.example`)
```
LLM_PROVIDER=openai          # openai | anthropic | ollama | custom
LLM_API_KEY=your_key_here
LLM_MODEL=gpt-4o             # or claude-opus-4-6, llama3, etc.
LLM_BASE_URL=                # optional, for custom/ollama endpoints
```

### Networks
- Development: Hardhat local network
- Testing: Base Sepolia testnet
- No mainnet deployment required for research

---

## 6. Paper Structure (AutoResearchClaw target output)

1. Introduction — problem, gap, contributions
2. Background — A2A protocols, x402, DID standards
3. MAEP Protocol Design — formal specification
4. Implementation — contracts, SDK architecture
5. Evaluation — 4 experiments
6. Discussion — limitations, trust model analysis
7. Related Work — Fetch.ai, Autonolas, Bittensor
8. Conclusion

---

## Open Questions (resolved)
- LLM backend: pluggable, user sets API key via `.env` ✓
- Chain: Hardhat local + Base Sepolia ✓
- Target venue: flexible, decide after completion ✓
- Conda env: new `web3_maep` env for special dependencies ✓
