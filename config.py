"""Model configuration and environment management for ADK Humanizer Agent."""

from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv
from google.adk.models.lite_llm import LiteLlm

# Find and load .env file without wiping existing system environment variables
_env_path = Path(__file__).resolve().parent / ".env"
if _env_path.exists():
    load_dotenv(dotenv_path=_env_path, override=False)


def get_configured_model() -> LiteLlm:
    """Instantiate and return the configured LiteLlm model adapter.

    Resolves between NVIDIA NIM (SLMs & LLMs), OpenRouter, and custom
    models configured via the HUMANIZER_MODEL environment variable.
    """
    model_name = os.getenv("HUMANIZER_MODEL", "nvidia_nim/google/gemma-4-31b-it").strip()

    # Pass API keys to environment if present in system or .env
    openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if openrouter_key:
        os.environ["OPENROUTER_API_KEY"] = openrouter_key

    nvidia_key = os.getenv("NVIDIA_API_KEY", "").strip()
    if nvidia_key:
        os.environ["NVIDIA_API_KEY"] = nvidia_key
        os.environ["NVIDIA_NIM_API_KEY"] = nvidia_key

    # Route NVIDIA NIM models through OpenAI-compatible endpoint with verified tool support
    if model_name.startswith("nvidia_nim/") or model_name.startswith("nvidia/"):
        clean_model = model_name.replace("nvidia_nim/", "")
        return LiteLlm(
            model=f"openai/{clean_model}",
            api_base="https://integrate.api.nvidia.com/v1",
            api_key=nvidia_key,
        )

    return LiteLlm(model=model_name)
