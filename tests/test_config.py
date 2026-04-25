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
