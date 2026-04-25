"""
Experiment 3: Trust assumption count per protocol.
Static analysis — outputs comparison table for paper.
Run: python experiments/trust_analysis.py
"""
import json
import os

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
    os.makedirs("experiments", exist_ok=True)
    with open("experiments/results_trust.json", "w") as f:
        json.dump(TRUST_ANALYSIS, f, indent=2)
    print("\nFull analysis saved to experiments/results_trust.json")
