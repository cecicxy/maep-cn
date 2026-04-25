import os
from dotenv import load_dotenv

load_dotenv()

def load_config() -> dict:
    provider = os.getenv("LLM_PROVIDER", "openai")
    api_key = os.getenv("LLM_API_KEY", "")
    model = os.getenv("LLM_MODEL", "gpt-4o")
    base_url = os.getenv("LLM_BASE_URL", "")

    if not api_key and provider != "ollama":
        raise ValueError("LLM_API_KEY is required (set in .env)")

    return {"provider": provider, "api_key": api_key, "model": model, "base_url": base_url}
