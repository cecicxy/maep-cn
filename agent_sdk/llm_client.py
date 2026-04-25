from openai import OpenAI
import anthropic

class LLMClient:
    def __init__(self, config: dict):
        self._config = config
        provider = config["provider"]

        if provider in ("openai", "ollama", "custom"):
            kwargs = {"api_key": config["api_key"]}
            if config.get("base_url"):
                kwargs["base_url"] = config["base_url"]
            elif provider == "ollama":
                kwargs["base_url"] = "http://localhost:11434/v1"
                kwargs["api_key"] = "ollama"
            self._client = OpenAI(**kwargs)
            self._provider_type = "openai"

        elif provider == "anthropic":
            self._client = anthropic.Anthropic(api_key=config["api_key"])
            self._provider_type = "anthropic"

        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def complete(self, prompt: str) -> str:
        model = self._config["model"]
        if self._provider_type == "openai":
            resp = self._client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
            )
            return resp.choices[0].message.content
        else:
            resp = self._client.messages.create(
                model=model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            return resp.content[0].text
