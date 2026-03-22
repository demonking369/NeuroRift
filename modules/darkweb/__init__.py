"""
Dark Web OSINT module for NeuroRift
Provides Robin integration for dark web intelligence gathering
"""

# Make Robin imports optional - don't break NeuroRift if langchain is missing
try:
    from .robin.runner import (
        run_darkweb_osint,
        ROBIN_DEFAULT_MODEL,
        get_robin_model_choices,
    )

    ROBIN_AVAILABLE = True
except ImportError as e:
    import logging

    logging.getLogger(__name__).warning(
        "Robin dark web module not available. Install langchain dependencies: "
        "pip install langchain-core langchain-openai llama-cpp-python[server]"
    )
    ROBIN_AVAILABLE = False

    # Provide stub functions
    def run_darkweb_osint(*args, **kwargs):
        raise ImportError(
            "Robin module requires langchain dependencies. "
            "Install with: pip install langchain-core langchain-openai llama-cpp-python[server] langchain-anthropic langchain-google-genai langchain-community"
        )

    ROBIN_DEFAULT_MODEL = "gpt4o"

    def get_robin_model_choices():
        return ["gpt4o"]


__all__ = [
    "run_darkweb_osint",
    "ROBIN_DEFAULT_MODEL",
    "get_robin_model_choices",
    "ROBIN_AVAILABLE",
]
