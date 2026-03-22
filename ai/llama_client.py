#!/usr/bin/env python3
"""NeuroRift v2 — llama.cpp OpenAI-compatible client."""

import json
import logging
import httpx
from typing import Any, Dict, List, Optional


class LlamaServerError(Exception):
    """Raised when llama.cpp server is unreachable or unhealthy."""


class LlamaClient:
    def __init__(self, base_url: str = "http://localhost:8080/v1", timeout: float = 300.0):
        self.base_url = base_url.rstrip("/")
        self.chat_url = f"{self.base_url}/chat/completions"
        self.health_url = f"{self.base_url.replace('/v1', '')}/health"
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)

    def check_health(self) -> None:
        """Check llama.cpp server is up. Raises LlamaServerError immediately if not."""
        try:
            r = httpx.get(self.health_url, timeout=5.0)
            if r.status_code != 200:
                raise LlamaServerError(
                    f"llama.cpp server unhealthy: HTTP {r.status_code}. "
                    "Ensure 'python -m llama_cpp.server' is running on port 8080."
                )
        except httpx.RequestError as e:
            raise LlamaServerError(
                f"llama.cpp server is unreachable at {self.health_url}. "
                f"Start it with: ./scripts/start_llama.sh\nError: {e}"
            ) from e

    async def generate_chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "hermes-2-pro-mistral-7b",
        temperature: float = 0.1,
        max_tokens: int = 4096,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Send a chat completion request. Returns parsed response dict or error dict."""
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.chat_url, json=payload)

                if response.status_code == 400 and "context window is full" in response.text.lower():
                    self.logger.error("Context overflow from llama.cpp.")
                    return {"error": "context_length_exceeded", "message": "Prompt exceeded 4096 token limit."}

                response.raise_for_status()
                data = response.json()

                if "choices" in data and data["choices"]:
                    msg = data["choices"][0].get("message", {})
                    if tools and "tool_calls" in msg:
                        return {"type": "tool_calls", "calls": msg["tool_calls"]}
                    return {"type": "text", "content": msg.get("content", "").strip()}
                return None

        except httpx.RequestError as e:
            self.logger.error("Network error: %s", e)
            return {"error": "network_failure", "message": str(e)}
        except Exception as e:
            self.logger.error("Unexpected error: %s", e)
            return {"error": "internal_failure", "message": str(e)}
