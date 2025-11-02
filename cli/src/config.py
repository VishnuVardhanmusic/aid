# src/config.py
from pathlib import Path
import os


# Default model and env var names. Update or override with environment variables.
MODEL_NAME = os.environ.get("MODEL_NAME", "anthropic.claude-3-7-sonnet-ep")
API_KEY_ENV = os.environ.get("OPENAI_API_KEY") or os.environ.get("API_KEY")
API_BASE = os.environ.get("OPENAI_API_BASE") or os.environ.get("API_BASE_URL")


# knowledge base dir
KB_DIR = Path(os.environ.get("KB_DIR", Path.cwd() / "knowledge_base"))


# CLI behavior
DEFAULT_PROMPT = os.environ.get("DEFAULT_PROMPT", "What is Artificial Intelligence?")


# Safety / limits
MAX_RULES_TO_PROCESS = int(os.environ.get("MAX_RULES_TO_PROCESS", "10"))