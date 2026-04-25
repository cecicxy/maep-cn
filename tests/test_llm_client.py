import pytest
from unittest.mock import patch, MagicMock
from agent_sdk.llm_client import LLMClient

def test_openai_client_call():
    cfg = {"provider": "openai", "api_key": "sk-test", "model": "gpt-4o", "base_url": ""}
    mock_openai_instance = MagicMock()
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "hello"
    mock_openai_instance.chat.completions.create.return_value = mock_response
    with patch("agent_sdk.llm_client.OpenAI", return_value=mock_openai_instance):
        client = LLMClient(cfg)
        result = client.complete("say hello")
    assert result == "hello"

def test_unknown_provider_raises():
    cfg = {"provider": "unknown", "api_key": "x", "model": "x", "base_url": ""}
    with pytest.raises(ValueError, match="Unsupported provider"):
        LLMClient(cfg)
