from openai import OpenAI
import anthropic

class LLMClient:
    def __init__(self, config: dict):
        self._config = config
        provider = config["provider"]

        ZHIPU_BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"
        MINIMAX_BASE_URL = "https://api.minimax.io/v1"

        if provider == "minimax":
            import httpx
            self._client = OpenAI(
                api_key=config["api_key"],
                base_url=config.get("base_url") or MINIMAX_BASE_URL,
                default_headers={"Authorization": f"Bearer {config['api_key']}"},
                http_client=httpx.Client(
                    headers={"Authorization": f"Bearer {config['api_key']}"},
                ),
            )
            self._provider_type = "openai"

        elif provider == "zhipu":
            self._client = OpenAI(api_key=config["api_key"], base_url=ZHIPU_BASE_URL)
            self._provider_type = "openai"

        elif provider in ("openai", "ollama", "custom"):
            kwargs = {"api_key": config["api_key"]}
            if config.get("base_url"):
                kwargs["base_url"] = config["base_url"]
            elif provider == "ollama":
                kwargs["base_url"] = "http://localhost:11434/v1"
                kwargs["api_key"] = "ollama"
            self._client = OpenAI(**kwargs)
            self._provider_type = "openai"

        elif provider == "anthropic":
            kwargs = {"api_key": config["api_key"]}
            if config.get("base_url"):
                kwargs["base_url"] = config["base_url"]
            self._client = anthropic.Anthropic(**kwargs)
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
            msg = resp.choices[0].message
            return msg.content or getattr(msg, "reasoning", None) or ""
        else:
            resp = self._client.messages.create(
                model=model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            return resp.content[0].text
