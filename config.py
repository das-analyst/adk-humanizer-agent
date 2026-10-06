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


def get_analytic_model() -> LiteLlm:
    """Instantiate and return the configured LiteLlm model adapter for analytical tasks (Critic/Diagnostic).
    
    Defaults to google/gemma-4-31b-it.
    """
    model_name = os.getenv("HUMANIZER_ANALYTIC_MODEL", "nvidia_nim/google/gemma-4-31b-it").strip()
    return _build_model(model_name)

def get_generative_model() -> LiteLlm:
    """Instantiate and return the configured LiteLlm model adapter for creative drafting tasks (Planner/Rewriter).
    
    Defaults to nvidia/nemotron-3-super-120b-a12b.
    """
    model_name = os.getenv("HUMANIZER_GENERATIVE_MODEL", "nvidia_nim/nvidia/nemotron-3-super-120b-a12b").strip()
    return _build_model(model_name)

def get_configured_model() -> LiteLlm:
    """Fallback for backwards compatibility, returns analytic model."""
    return get_analytic_model()

def _build_model(model_name: str) -> LiteLlm:
    """Helper to build the LiteLlm instance with necessary API keys."""
    # Pass API keys to environment if present in system or .env
    openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if openrouter_key:
        os.environ["OPENROUTER_API_KEY"] = openrouter_key

    nvidia_key = os.getenv("NVIDIA_API_KEY", "").strip()
    if nvidia_key:
        os.environ["NVIDIA_API_KEY"] = nvidia_key
        os.environ["NVIDIA_NIM_API_KEY"] = nvidia_key

    # Route Ollama models through local Ollama server (OpenAI-compatible /v1 endpoint)
    if model_name.startswith("ollama/") or model_name.startswith("ollama:"):
        clean_model = model_name.replace("ollama/", "").replace("ollama:", "")
        ollama_base = os.getenv("OLLAMA_API_BASE", "http://127.0.0.1:11434").rstrip("/")
        return LiteLlm(
            model=f"openai/{clean_model}",
            api_base=f"{ollama_base}/v1",
            api_key="ollama",
        )

    # Route NVIDIA NIM models through OpenAI-compatible endpoint with verified tool support
    if model_name.startswith("nvidia_nim/") or model_name.startswith("nvidia/"):
        clean_model = model_name.replace("nvidia_nim/", "")
        if clean_model.startswith("nvidia/"):
            clean_model = clean_model # Already has nvidia/ prefix
        return LiteLlm(
            model=f"openai/{clean_model}",
            api_base="https://integrate.api.nvidia.com/v1",
            api_key=nvidia_key,
        )

    return LiteLlm(model=model_name)
