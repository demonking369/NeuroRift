import os
from pathlib import Path
from dotenv import load_dotenv


def _load_env():
    """Attempt to load environment variables from common NeuroRift locations."""
    candidate_paths = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parents[3] / ".env",  # project root
        Path.home() / ".neurorift" / ".env",
    ]

    loaded = False
    for env_path in candidate_paths:
        if env_path.is_file():
            load_dotenv(env_path, override=False)
            loaded = True

    if not loaded:
        # Fallback to default behaviour (walk up the tree)
        load_dotenv()


_load_env()

# Configuration variables loaded from the .env file
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
LLAMA_BASE_URL = os.getenv("LLAMA_BASE_URL")
LLAMA_MAIN_MODEL = os.getenv("LLAMA_MAIN_MODEL")
LLAMA_ASSISTANT_MODEL = os.getenv("LLAMA_ASSISTANT_MODEL")
