# src/config.py
"""
Configuration file for the Klocwork AI Fixer CLI.

This loads model-related environment variables that control how Aider (or any LLM)
will be invoked. Keeping config centralized ensures the engine module stays clean.

Usage:
    from src.config import MODEL_NAME, API_KEY, API_BASE_URL
"""

import os
from dataclasses import dataclass

@dataclass
class AppConfig:
    MODEL_NAME: str
    API_KEY: str
    API_BASE_URL: str


def load_config() -> AppConfig:
    """
    Loads config from environment variables. Ensure these are set in your .env.

    Expected environment variables:
        MODEL_NAME      - e.g., "gpt-4.1-mini", "claude-3.7-sonnet"
        API_KEY         - Your model provider API key
        API_BASE_URL    - Optional base URL override (LiteLLM, proxy, etc.)

    Returns:
        AppConfig object
    """
    model = os.getenv("MODEL_NAME", "gpt-4.1-mini")
    key = os.getenv("API_KEY", "")
    base = os.getenv("API_BASE_URL", "")  # empty means use default of the provider

    if not key:
        print("[warn] API_KEY not set. Calls to the model will fail until provided.")

    return AppConfig(MODEL_NAME=model, API_KEY=key, API_BASE_URL=base)


# Make config available at import
CONFIG = load_config()
