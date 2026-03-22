# ╔══════════════════════════════════════════════════════════╗
# ║ NeuroRift - Built with Blood by DemonKing369.0 👑        ║
# ║ GitHub: https://github.com/Arunking9                     ║
# ║ AI-Powered Security Framework for Bug Bounty Warriors ⚔️║
# ╚══════════════════════════════════════════════════════════╝

#!/usr/bin/env python3
"""
NeuroRift LLM Engine
Handles model management, fallbacks, and caching for AI operations using LlamaClient
"""

import json
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any
from functools import lru_cache

from .llama_client import LlamaClient


class LLMEngine:
    def __init__(self, config_path: Optional[Path] = None):
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config(config_path)
        self.models = self._initialize_models()
        self.current_model = self.models[0]  # Start with preferred model
        self.response_cache = {}
        self.llama_client = LlamaClient(base_url="http://localhost:8080/v1")

    def _load_config(self, config_path: Optional[Path] = None) -> Dict:
        """Load LLM configuration"""
        if not config_path:
            config_path = Path.home() / ".neurorift" / "configs" / "llm_config.json"

        default_config = {
            "preferred_model": "hermes-2-pro-mistral-7b",
            "fallback_models": ["hermes-2-pro-mistral-7b"],
            "cache_size": 100,
            "timeout": 180,
            "max_retries": 3,
            "retry_delay": 2,
        }

        try:
            if config_path.exists():
                with open(config_path) as f:
                    return {**default_config, **json.load(f)}
            return default_config
        except Exception as e:
            self.logger.error("Error loading LLM config: %s", e)
            return default_config

    def _initialize_models(self) -> List[str]:
        """Initialize available models"""
        available_models = [self.config["preferred_model"]]
        for model in self.config["fallback_models"]:
            if model not in available_models:
                available_models.append(model)

        return available_models

    @lru_cache(maxsize=100)
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Optional[str]:
        """Generate text (wrapper for query)"""
        return await self.query(prompt, system_prompt=system_prompt, model=model)

    async def query(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        use_cache: bool = True,
    ) -> Optional[str]:
        if not model:
            model = self.current_model

        # Check cache if enabled
        cache_key = f"{model}:{prompt}:{system_prompt}"
        if use_cache and cache_key in self.response_cache:
            return self.response_cache[cache_key]

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        for attempt in range(self.config["max_retries"]):
            try:
                result_data = await self.llama_client.generate_chat(
                    messages=messages, model=model, temperature=0.7, max_tokens=4096
                )

                if result_data and "error" not in result_data:
                    result = result_data.get("content", "")
                    if use_cache:
                        self.response_cache[cache_key] = result
                    return result
                elif result_data and "error" in result_data:
                    self.logger.warning("LlamaClient error: %s", result_data["message"])

            except Exception as e:
                self.logger.error("Error querying model %s: %s", model, e)

            # Try next model if available
            if model in self.models:
                current_index = self.models.index(model)
                if current_index + 1 < len(self.models):
                    model = self.models[current_index + 1]
                    self.logger.info("Switching to fallback model: %s", model)
                else:
                    break

            await asyncio.sleep(self.config["retry_delay"])

        return None

    def clear_cache(self):
        """Clear the response cache"""
        self.response_cache.clear()
        try:
            self.generate.cache_clear()
        except AttributeError:
            pass

    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        return self.models.copy()

    def set_preferred_model(self, model: str) -> bool:
        """Set preferred model if available"""
        if model in self.models:
            self.current_model = model
            return True
        return False
