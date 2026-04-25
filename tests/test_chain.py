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
