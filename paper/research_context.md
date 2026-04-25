# MAEP Research Context for AutoResearchClaw

## Title (draft)
MAEP: A Minimum Viable Agent-to-Agent Economic Protocol with Decentralized Identity and Trustless Payment Settlement

## Abstract (draft)
Existing agent communication protocols such as Google A2A and Coinbase x402 lack two critical primitives for autonomous economic activity: decentralized agent identity and trustless micropayment settlement. We present MAEP, a Minimum Viable Agent-to-Agent Economic Protocol that addresses these gaps through three Ethereum smart contracts (AgentRegistry, PaymentChannel, ResultAttestation) and a Python Agent SDK with pluggable LLM backends. We evaluate MAEP against x402 and Google A2A on three dimensions: end-to-end latency, on-chain Gas cost, and trust assumption count. Our experiments show MAEP reduces trust assumptions to a single party (Ethereum consensus) compared to 2-3 for existing protocols. We provide an open-source reference implementation and end-to-end scenario demonstrations.

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
