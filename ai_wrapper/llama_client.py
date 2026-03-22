# ╔══════════════════════════════════════════════════════════╗
# ║ NeuroRift - Built with Blood by DemonKing369.0 👑        ║
# ║ GitHub: https://github.com/Arunking9                     ║
# ║ AI-Powered Security Framework for Bug Bounty Warriors ⚔️║
# ╚══════════════════════════════════════════════════════════╝

#!/usr/bin/env python3
"""
NeuroRift llama.cpp HTTP Client
OpenAI-compatible wrapper around local llama.cpp server.
"""

import json
import logging
import httpx
from typing import Dict, List, Optional, Any


class LlamaClient:
    def __init__(self, base_url: str = "http://localhost:8080/v1"):
        self.logger = logging.getLogger(__name__)
        self.base_url = base_url
        self.chat_url = f"{self.base_url}/chat/completions"
        self.timeout = 300.0  # Local models can be slow

    async def generate_chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "hermes-2-pro-mistral-7b",
        temperature: float = 0.1,
        max_tokens: int = 4096,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Query the local llama.cpp server using the OpenAI chat completions schema.
        Handles graceful context overflow and tool calling integration.
        """
        payload = {
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

                # Handle context overflow (llama.cpp typical 400 error or specific internal msg)
                if (
                    response.status_code == 400
                    and "context window is full" in response.text.lower()
                ):
                    self.logger.error(
                        "Context overflow detected inside llama.cpp server."
                    )
                    return {
                        "error": "context_length_exceeded",
                        "message": "The prompt exceeded the 4096 token limit.",
                    }

                response.raise_for_status()
                data = response.json()

                # Extract first choice
                if "choices" in data and len(data["choices"]) > 0:
                    message_data = data["choices"][0].get("message", {})

                    # Process structured tool calls if requested
                    if tools and "tool_calls" in message_data:
                        return {
                            "type": "tool_calls",
                            "calls": message_data["tool_calls"],
                        }

                    return {
                        "type": "text",
                        "content": message_data.get("content", "").strip(),
                    }

                return None

        except httpx.RequestError as e:
            self.logger.error("Network error communicating with llama.cpp: %s", e)
            return {"error": "network_failure", "message": str(e)}
        except Exception as e:
            self.logger.error("Unexpected error in LlamaClient: %s", e)
            return {"error": "internal_failure", "message": str(e)}
