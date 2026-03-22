"""
LLM utility functions and handlers for Robin
"""

from typing import Callable, Optional, List
from urllib.parse import urljoin

import logging
import requests
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.callbacks.base import BaseCallbackHandler

# Fix imports to work both as module and when run directly
try:
    from .config import LLAMA_BASE_URL, LLAMA_MAIN_MODEL, LLAMA_ASSISTANT_MODEL
except ImportError:
    from config import LLAMA_BASE_URL, LLAMA_MAIN_MODEL, LLAMA_ASSISTANT_MODEL


class BufferedStreamingHandler(BaseCallbackHandler):
    def __init__(
        self,
        buffer_limit: int = 60,
        ui_callback: Optional[Callable[[str], None]] = None,
    ):
        self.buffer = ""
        self.buffer_limit = buffer_limit
        self.ui_callback = ui_callback

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        self.buffer += token
        if "\n" in token or len(self.buffer) >= self.buffer_limit:
            # print(self.buffer, end="", flush=True)  # Disabled to prevent terminal spam
            if self.ui_callback:
                self.ui_callback(self.buffer)
            self.buffer = ""

    def on_llm_end(self, response, **kwargs) -> None:
        if self.buffer:
            # print(self.buffer, end="", flush=True)  # Disabled to prevent terminal spam
            if self.ui_callback:
                self.ui_callback(self.buffer)
            self.buffer = ""


def _normalize_model_name(name: str) -> str:
    return name.strip().lower()


def _get_llama_base_url() -> str:
    # Default to localhost if not specified
    url = LLAMA_BASE_URL or "http://localhost:8080/v1"
    return url.rstrip("/") + "/"


# --- Configuration Data ---
# Instantiate common dependencies once
_common_callbacks = [BufferedStreamingHandler(buffer_limit=60)]

# Define common parameters for most LLMs
_common_llm_params = {
    "temperature": 0,
    "streaming": True,
    "callbacks": _common_callbacks,
}

# Map input model choices (lowercased) to their configuration
# Each config includes the class and any model-specific constructor parameters
_llm_config_map = {
    "gpt-4o": {"class": ChatOpenAI, "constructor_params": {"model_name": "gpt-4o"}},
    "gpt-4.1": {"class": ChatOpenAI, "constructor_params": {"model_name": "gpt-4.1"}},
    "gpt-5.1": {"class": ChatOpenAI, "constructor_params": {"model_name": "gpt-5.1"}},
    "gpt-5-mini": {
        "class": ChatOpenAI,
        "constructor_params": {"model_name": "gpt-5-mini"},
    },
    "gpt-5-nano": {
        "class": ChatOpenAI,
        "constructor_params": {"model_name": "gpt-5-nano"},
    },
    "claude-3-5-sonnet-latest": {
        "class": ChatAnthropic,
        "constructor_params": {"model": "claude-3-5-sonnet-latest"},
    },
    "claude-sonnet-4-5": {
        "class": ChatAnthropic,
        "constructor_params": {"model": "claude-sonnet-4-5"},
    },
    "claude-sonnet-4-0": {
        "class": ChatAnthropic,
        "constructor_params": {"model": "claude-sonnet-4-0"},
    },
    "gemini-2.5-flash": {
        "class": ChatGoogleGenerativeAI,
        "constructor_params": {"model": "gemini-2.5-flash"},
    },
    "gemini-2.5-flash-lite": {
        "class": ChatGoogleGenerativeAI,
        "constructor_params": {"model": "gemini-2.5-flash-lite"},
    },
    "gemini-2.5-pro": {
        "class": ChatGoogleGenerativeAI,
        "constructor_params": {"model": "gemini-2.5-pro"},
    },
    "llama3.2": {
        "class": ChatOpenAI,
        "constructor_params": {
            "model": "llama3.2:latest",
            "base_url": _get_llama_base_url(),
            "api_key": "none",
        },
    },
    "llama3.1": {
        "class": ChatOpenAI,
        "constructor_params": {
            "model": "llama3.1:latest",
            "base_url": _get_llama_base_url(),
            "api_key": "none",
        },
    },
    "gemma3": {
        "class": ChatOpenAI,
        "constructor_params": {
            "model": "gemma3:latest",
            "base_url": _get_llama_base_url(),
            "api_key": "none",
        },
    },
    "deepseek-r1": {
        "class": ChatOpenAI,
        "constructor_params": {
            "model": "deepseek-r1:latest",
            "base_url": _get_llama_base_url(),
            "api_key": "none",
        },
    },
    # Add more models here easily:
    # 'mistral7b': {
    #     'class': Chatllama.cpp,
    #     'constructor_params': {'model': 'mistral:7b', 'base_url': LLAMA_BASE_URL}
    # },
    # 'gpt3.5': {
    #      'class': ChatOpenAI,
    #      'constructor_params': {'model_name': 'gpt-3.5-turbo', 'base_url': LLAMA_BASE_URL}
    # }
}


def fetch_llama_models() -> List[str]:
    """
    Retrieve the list of locally available llama.cpp models by querying the llama.cpp HTTP API.
    Returns an empty list if the API isn't reachable or the base URL is not defined.
    """
    base_url = _get_llama_base_url()
    if not base_url:
        return []

    try:
        resp = requests.get(urljoin(base_url, "models"), timeout=3)
        resp.raise_for_status()
        models = resp.json().get("data", [])
        return [m.get("id") for m in models if m.get("id")]
    except (requests.RequestException, ValueError) as e:
        logging.debug(f"Failed to fetch llama_cpp models from {base_url}: {e}")
        return []


def get_model_choices() -> List[str]:
    """
    Combine the statically configured cloud models with the locally available llama.cpp models.
    """
    base_models = list(_llm_config_map.keys())
    dynamic_models = fetch_llama_models()

    normalized = {_normalize_model_name(m): m for m in base_models}

    # Add models from .env if they aren't already there
    for env_model in [LLAMA_MAIN_MODEL, LLAMA_ASSISTANT_MODEL]:
        if env_model:
            key = _normalize_model_name(env_model)
            if key not in normalized:
                normalized[key] = env_model

    for dm in dynamic_models:
        key = _normalize_model_name(dm)
        if key not in normalized:
            normalized[key] = dm

    # Preserve the order: original base models first, then the dynamic ones in alphabetical order
    ordered_dynamic = sorted(
        [name for key, name in normalized.items() if name not in base_models],
        key=_normalize_model_name,
    )
    return base_models + ordered_dynamic


def resolve_model_config(model_choice: str):
    """
    Resolve a model choice (case-insensitive) to the corresponding configuration.
    Supports both the predefined remote models and any locally installed llama.cpp models.
    """
    model_choice_lower = _normalize_model_name(model_choice)
    config = _llm_config_map.get(model_choice_lower)
    if config:
        return config

    # Check if it matches any of the models from .env
    for env_model in [LLAMA_MAIN_MODEL, LLAMA_ASSISTANT_MODEL]:
        if env_model and _normalize_model_name(env_model) == model_choice_lower:
            return {
                "class": ChatOpenAI,
                "constructor_params": {
                    "model_name": env_model,
                    "base_url": _get_llama_base_url(),
                    "api_key": "none",
                },
            }

    # Check against dynamic models from llama.cpp API
    for llama_model in fetch_llama_models():
        if _normalize_model_name(llama_model) == model_choice_lower:
            return {
                "class": ChatOpenAI,
                "constructor_params": {
                    "model_name": llama_model,
                    "base_url": _get_llama_base_url(),
                    "api_key": "none",
                },
            }

    return None
