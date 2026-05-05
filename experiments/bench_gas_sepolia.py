"""
Experiment 2b: Gas cost on Base Sepolia testnet (real network).
Requires: .env with DEPLOYER_PRIVATE_KEY, BASE_SEPOLIA_RPC_URL, and contract addresses.
Run: python experiments/bench_gas_sepolia.py
"""
import json
import os
import sys
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from web3 import Web3
from eth_account import Account

load_dotenv()

RPC_URL = os.getenv("BASE_SEPOLIA_RPC_URL", "https://sepolia.base.org")
PRIVATE_KEY = os.getenv("DEPLOYER_PRIVATE_KEY", "")
REGISTRY_ADDR = os.getenv("AGENT_REGISTRY_ADDRESS", "")
CHANNEL_ADDR = os.getenv("PAYMENT_CHANNEL_ADDRESS", "")
ATTEST_ADDR = os.getenv("RESULT_ATTESTATION_ADDRESS", "")

def load_abi(name):
    path = f"contracts/abi/{name}.json"
    with open(path) as f:
        return json.load(f)

def send_tx(w3, account, tx):
    signed = account.sign_transaction(tx)
    raw = signed.raw_transaction if hasattr(signed, 'raw_transaction') else signed.rawTransaction
    tx_hash = w3.eth.send_raw_transaction(raw)
    print(f"  tx: {tx_hash.hex()} ... waiting")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    return receipt

if __name__ == "__main__":
    if not PRIVATE_KEY or not REGISTRY_ADDR:
        print("ERROR: Set DEPLOYER_PRIVATE_KEY and contract addresses in .env")
        sys.exit(1)

    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    assert w3.is_connected(), f"Cannot connect to {RPC_URL}"

    deployer = Account.from_key(PRIVATE_KEY)
    bal = w3.eth.get_balance(deployer.address)
    print(f"Account: {deployer.address}")
    print(f"Balance: {w3.from_wei(bal, 'ether'):.6f} ETH")
    print(f"Network: Base Sepolia (chainId={w3.eth.chain_id})\n")

    registry = w3.eth.contract(address=REGISTRY_ADDR, abi=load_abi("AgentRegistry"))
    channel  = w3.eth.contract(address=CHANNEL_ADDR,  abi=load_abi("PaymentChannel"))
    attest   = w3.eth.contract(address=ATTEST_ADDR,   abi=load_abi("ResultAttestation"))

    gas_price = w3.eth.gas_price
    print(f"Gas price: {w3.from_wei(gas_price, 'gwei'):.4f} gwei\n")

    gas_report = {}

    # REGISTER
    print("Stage 1: REGISTER")
    nonce = w3.eth.get_transaction_count(deployer.address)
    tx = registry.functions.register('{"task_types":["data_analysis"]}').build_transaction({
        "from": deployer.address,
        "value": w3.to_wei(0.0001, "ether"),
        "nonce": nonce,
        "gasPrice": gas_price,
        "gas": 200000,
    })
    receipt = send_tx(w3, deployer, tx)
    gas_report["REGISTER"] = receipt.gasUsed
    print(f"  gas used: {receipt.gasUsed:,}\n")
    time.sleep(2)

    # DELEGATE
    print("Stage 2: DELEGATE (lock payment)")
    task_id = w3.keccak(text="sepolia-bench-task-001")
    deadline = w3.eth.get_block("latest")["timestamp"] + 3600
    nonce = w3.eth.get_transaction_count(deployer.address)
    tx = channel.functions.lock(task_id, deployer.address, deadline).build_transaction({
        "from": deployer.address,
        "value": w3.to_wei(0.00005, "ether"),
        "nonce": nonce,
        "gasPrice": gas_price,
        "gas": 200000,
    })
    receipt = send_tx(w3, deployer, tx)
    gas_report["DELEGATE"] = receipt.gasUsed
    print(f"  gas used: {receipt.gasUsed:,}\n")
    time.sleep(2)

    # EXECUTE (attest result)
    print("Stage 3: EXECUTE (attest result hash)")
    result_hash = w3.keccak(text="sepolia result data content")
    nonce = w3.eth.get_transaction_count(deployer.address)
    tx = attest.functions.attest(task_id, result_hash).build_transaction({
        "from": deployer.address,
        "nonce": nonce,
        "gasPrice": gas_price,
        "gas": 200000,
    })
    receipt = send_tx(w3, deployer, tx)
    gas_report["EXECUTE"] = receipt.gasUsed
    print(f"  gas used: {receipt.gasUsed:,}\n")
    time.sleep(2)

    # SETTLE (release payment)
    print("Stage 4: SETTLE (release payment)")
    nonce = w3.eth.get_transaction_count(deployer.address)
    tx = channel.functions.release(task_id).build_transaction({
        "from": deployer.address,
        "nonce": nonce,
        "gasPrice": gas_price,
        "gas": 200000,
    })
    receipt = send_tx(w3, deployer, tx)
    gas_report["SETTLE"] = receipt.gasUsed
    print(f"  gas used: {receipt.gasUsed:,}\n")

    total = sum(gas_report.values())
    print(f"\n{'Stage':<12} {'Gas Used (Sepolia)':>20}")
    print("-" * 34)
    for stage, gas in gas_report.items():
        print(f"{stage:<12} {gas:>20,}")
    print(f"{'TOTAL':<12} {total:>20,}")

    # Load local results for comparison
    try:
        with open("experiments/results_gas.json") as f:
            local = json.load(f)
        local_stages = local.get("gas_per_stage", {})
        print(f"\n{'Stage':<12} {'Hardhat (local)':>18} {'Base Sepolia':>14} {'Match':>8}")
        print("-" * 56)
        for stage in gas_report:
            local_gas = local_stages.get(stage, "N/A")
            match = "OK" if local_gas == gas_report[stage] else f"D{gas_report[stage]-local_gas:+d}"
            print(f"{stage:<12} {str(local_gas):>18} {gas_report[stage]:>14,} {match:>8}")
    except FileNotFoundError:
        pass

    result = {
        "network": "base_sepolia",
        "chain_id": w3.eth.chain_id,
        "gas_price_gwei": float(w3.from_wei(gas_price, "gwei")),
        "gas_per_stage": gas_report,
        "total_gas": total,
    }
    with open("experiments/results_gas_sepolia.json", "w") as f:
        json.dump(result, f, indent=2)
    print("\nResults saved to experiments/results_gas_sepolia.json")
