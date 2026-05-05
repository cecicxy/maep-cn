"""Configuration loader for MAEP-CN."""

import os
from dotenv import load_dotenv


def load_config() -> dict:
    load_dotenv()
    provider = os.getenv("LLM_PROVIDER", "openai")
    api_key = os.getenv("LLM_API_KEY", "")
    model = os.getenv("LLM_MODEL", "gpt-4o")
    base_url = os.getenv("LLM_BASE_URL", "")

    if not api_key and provider != "ollama":
        raise ValueError("LLM_API_KEY is required (unless using ollama)")

    return {
        "provider": provider,
        "api_key": api_key,
        "model": model,
        "base_url": base_url,
        "db_path": os.getenv("DB_PATH", "maep.db"),
        "min_deposit_cents": int(os.getenv("MIN_DEPOSIT_CENTS", "1000")),
    }
