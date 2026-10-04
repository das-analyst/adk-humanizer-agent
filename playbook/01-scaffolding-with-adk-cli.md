# Playbook 01: Scaffolding Multi-Agent Systems with the ADK CLI

> **Part of the ADK Multi-Agent Text Humanizer Development Playbook**  
> **Tooling:** Google Agent Development Kit (`google-adk`), Python 3.11+, LiteLLM

---

## 1. Environment Setup & Prerequisites

Google ADK requires Python 3.11 or 3.12. We recommend using `uv` or standard Python `venv`:

```bash
# Clone the repository
git clone https://github.com/das-analyst/adk-humanizer-agent.git
cd adk-humanizer-agent

# Create virtual environment
python -m venv .venv

# Activate on Windows PowerShell:
.venv\Scripts\Activate.ps1
# Activate on Linux / macOS:
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install google-adk fastmcp litellm python-dotenv pytest
```

---

## 2. Scaffolding Agents with the ADK CLI

The Google ADK CLI provides the `adk create` command to scaffold agent directories with required boilerplate and module structure:

```bash
# Verify the ADK CLI is available
adk --help
```

To reproduce the multi-agent hierarchy from scratch, scaffold each specialist under the `agents/` directory:

```bash
# 1. Root Orchestrator
adk create agents/humanizer_orchestrator

# 2. Forensic Diagnostic Specialist
adk create agents/diagnostic_agent

# 3. Cadence & Rhythm Architect
adk create agents/style_planner

# 4. Master Prose Stylist
adk create agents/rewriter_agent

# 5. Quality Gate & Fidelity Auditor
adk create agents/critic_agent
```

### Generated Agent File Anatomy
Each invocation of `adk create <agent_name>` produces:
```text
agents/<agent_name>/
├── __init__.py        # Exports `root_agent` for discovery by ADK Web & parent agents
└── agent.py           # Core agent implementation & instructions
```

> [!IMPORTANT]
> **The `root_agent` Export Rule:**  
> The ADK Web server (`adk web`) and parent orchestrators inspect modules for an instance named exactly `root_agent`. Never rename `root_agent` in `agent.py` or omit its export in `__init__.py`.

---

## 3. Configuring Multi-Model Providers via LiteLLM

The system uses `google.adk.models.lite_llm.LiteLlm` to support **NVIDIA NIM**, **OpenRouter**, and **Google Gemini** transparently.

### The Central Model Configurator (`config.py`):
```python
import os
from pathlib import Path
from dotenv import load_dotenv
from google.adk.models.lite_llm import LiteLlm

_env_path = Path(__file__).resolve().parent / ".env"
if _env_path.exists():
    load_dotenv(dotenv_path=_env_path, override=False)

def get_configured_model() -> LiteLlm:
    """Instantiate LiteLlm model adapter supporting NVIDIA NIM and OpenRouter."""
    model_name = os.getenv("HUMANIZER_MODEL", "nvidia_nim/google/gemma-4-31b-it").strip()
    
    nvidia_key = os.getenv("NVIDIA_API_KEY", "").strip()
    if nvidia_key:
        os.environ["NVIDIA_API_KEY"] = nvidia_key
        os.environ["NVIDIA_NIM_API_KEY"] = nvidia_key

    # Route NVIDIA NIM models through OpenAI-compatible endpoint
    if model_name.startswith("nvidia_nim/") or model_name.startswith("nvidia/"):
        clean_model = model_name.replace("nvidia_nim/", "")
        return LiteLlm(
            model=f"openai/{clean_model}",
            api_base="https://integrate.api.nvidia.com/v1",
            api_key=nvidia_key,
        )

    return LiteLlm(model=model_name)
```

### Environment Configuration (`.env`):
```bash
# NVIDIA NIM (Enterprise Inference)
NVIDIA_API_KEY="nvapi-your-key-here"

# OpenRouter (Supports standard and :free tier models)
OPENROUTER_API_KEY="sk-or-v1-your-key-here"

# Selected Model Architecture:
HUMANIZER_MODEL="nvidia_nim/google/gemma-4-31b-it"
# Or: HUMANIZER_MODEL="openrouter/meta-llama/llama-3.3-70b-instruct"
```
