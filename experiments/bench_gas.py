"""
Experiment 2: Gas cost per contract operation.
Requires: npx hardhat node running in another terminal (port 8545).
Run: python experiments/bench_gas.py
"""
import json
import subprocess
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web3 import Web3
from eth_account import Account

RPC_URL = "http://127.0.0.1:8545"
# Standard Hardhat test accounts (deterministic)
HARDHAT_ACCOUNTS = [
    "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",
    "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d",
    "0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a",
]

def load_artifact(name):
    path = f"artifacts/contracts/{name}.sol/{name}.json"
    with open(path) as f:
        return json.load(f)

def deploy_contracts(w3, deployer):
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

    registry = w3.eth.contract(
        address=contracts["AgentRegistry"]["address"],
        abi=contracts["AgentRegistry"]["abi"]
    )
    tx = registry.functions.register('{"task_types":["data_analysis"]}').build_transaction({
        "from": agent1.address,
        "value": w3.to_wei(0.01, "ether"),
        "nonce": w3.eth.get_transaction_count(agent1.address),
        "gas": 200000,
        "gasPrice": w3.to_wei("1", "gwei"),
    })
    signed = agent1.sign_transaction(tx)
    raw_tx = signed.rawTransaction if hasattr(signed, 'rawTransaction') else signed.raw_transaction
    receipt = w3.eth.wait_for_transaction_receipt(w3.eth.send_raw_transaction(raw_tx))
    gas_report["REGISTER"] = receipt.gasUsed

    channel = w3.eth.contract(
        address=contracts["PaymentChannel"]["address"],
        abi=contracts["PaymentChannel"]["abi"]
    )
    task_id = w3.keccak(text="bench-task-001")
    deadline = w3.eth.get_block("latest")["timestamp"] + 3600
    tx = channel.functions.lock(task_id, agent2.address, deadline).build_transaction({
        "from": agent1.address,
        "value": w3.to_wei(0.05, "ether"),
        "nonce": w3.eth.get_transaction_count(agent1.address),
        "gas": 200000,
        "gasPrice": w3.to_wei("1", "gwei"),
    })
    signed = agent1.sign_transaction(tx)
    raw_tx = signed.rawTransaction if hasattr(signed, 'rawTransaction') else signed.raw_transaction
    receipt = w3.eth.wait_for_transaction_receipt(w3.eth.send_raw_transaction(raw_tx))
    gas_report["DELEGATE"] = receipt.gasUsed

    attestation = w3.eth.contract(
        address=contracts["ResultAttestation"]["address"],
        abi=contracts["ResultAttestation"]["abi"]
    )
    result_hash = w3.keccak(text="result data content")
    tx = attestation.functions.attest(task_id, result_hash).build_transaction({
        "from": agent2.address,
        "nonce": w3.eth.get_transaction_count(agent2.address),
        "gas": 200000,
        "gasPrice": w3.to_wei("1", "gwei"),
    })
    signed = agent2.sign_transaction(tx)
    raw_tx = signed.rawTransaction if hasattr(signed, 'rawTransaction') else signed.raw_transaction
    receipt = w3.eth.wait_for_transaction_receipt(w3.eth.send_raw_transaction(raw_tx))
    gas_report["EXECUTE"] = receipt.gasUsed

    tx = channel.functions.release(task_id).build_transaction({
        "from": agent1.address,
        "nonce": w3.eth.get_transaction_count(agent1.address),
        "gas": 200000,
        "gasPrice": w3.to_wei("1", "gwei"),
    })
    signed = agent1.sign_transaction(tx)
    raw_tx = signed.rawTransaction if hasattr(signed, 'rawTransaction') else signed.raw_transaction
    receipt = w3.eth.wait_for_transaction_receipt(w3.eth.send_raw_transaction(raw_tx))
    gas_report["SETTLE"] = receipt.gasUsed

    return gas_report

if __name__ == "__main__":
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        print("ERROR: Hardhat node not running. Start with: npx hardhat node")
        sys.exit(1)

    deployer = Account.from_key(HARDHAT_ACCOUNTS[0])
    agent1 = Account.from_key(HARDHAT_ACCOUNTS[1])
    agent2 = Account.from_key(HARDHAT_ACCOUNTS[2])
    w3.eth.default_account = deployer.address

    print("Compiling contracts...")
    subprocess.run("npx hardhat compile", check=True, capture_output=True, cwd=os.getcwd(), shell=True)

    print("Deploying contracts to local Hardhat node...")
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

    os.makedirs("experiments", exist_ok=True)
    with open("experiments/results_gas.json", "w") as f:
        json.dump({
            "gas_per_stage": gas_report,
            "contracts": {k: v["deploy_gas"] for k, v in contracts.items()}
        }, f, indent=2)
    print("\nResults saved to experiments/results_gas.json")
