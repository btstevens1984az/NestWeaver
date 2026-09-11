"""Local Ollama LLM client — privacy-first, no cloud required."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class LLMConfig:
    base_url: str = "http://127.0.0.1:11434"
    model: str = "llama3.2:3b"
    timeout_s: float = 60.0
    system_prompt: str = (
        "You are NestWeaver, a helpful home companion robot. "
        "Keep answers brief. Prefer local actions over cloud services. "
        "Never invent sensor readings you were not given."
    )


class OllamaClient:
    """Minimal chat + generate client for Ollama's HTTP API."""

    def __init__(self, config: LLMConfig | None = None) -> None:
        self.config = config or LLMConfig()
        self._client = httpx.Client(base_url=self.config.base_url, timeout=self.config.timeout_s)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> OllamaClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def health(self) -> bool:
        try:
            r = self._client.get("/api/tags")
            return r.status_code == 200
        except httpx.HTTPError:
            return False

    def list_models(self) -> list[str]:
        r = self._client.get("/api/tags")
        r.raise_for_status()
        data = r.json()
        return [m.get("name", "") for m in data.get("models", [])]

    def chat(self, user_message: str, context: dict[str, Any] | None = None) -> str:
        messages = [
            {"role": "system", "content": self.config.system_prompt},
        ]
        if context:
            messages.append(
                {
                    "role": "system",
                    "content": f"Robot context (local only): {context}",
                }
            )
        messages.append({"role": "user", "content": user_message})
        payload = {
            "model": self.config.model,
            "messages": messages,
            "stream": False,
        }
        r = self._client.post("/api/chat", json=payload)
        r.raise_for_status()
        data = r.json()
        return data.get("message", {}).get("content", "")

    def generate(self, prompt: str) -> str:
        payload = {"model": self.config.model, "prompt": prompt, "stream": False}
        r = self._client.post("/api/generate", json=payload)
        r.raise_for_status()
        return r.json().get("response", "")


class OfflineEchoLLM:
    """Fallback when Ollama is not running — keeps demos / tests offline-capable."""

    def health(self) -> bool:
        return True

    def chat(self, user_message: str, context: dict[str, Any] | None = None) -> str:
        room = (context or {}).get("room", "the house")
        return (
            f"(offline) I heard: “{user_message}”. "
            f"When Ollama is running locally I can plan tidy/fetch tasks in {room}."
        )
