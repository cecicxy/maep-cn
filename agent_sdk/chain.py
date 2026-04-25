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
