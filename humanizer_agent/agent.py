"""Legacy / Direct Compatibility Entrypoint for Humanizer Agent.

Re-exports the modular root orchestrator from agents.humanizer_orchestrator.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure root directory is on sys.path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from agents.humanizer_orchestrator.agent import root_agent
from agents.diagnostic_agent.agent import root_agent as diagnostic_agent
from agents.style_planner.agent import root_agent as style_planner_agent
from agents.rewriter_agent.agent import root_agent as rewriter_agent
from agents.critic_agent.agent import root_agent as critic_agent

__all__ = [
    "root_agent",
    "diagnostic_agent",
    "style_planner_agent",
    "rewriter_agent",
    "critic_agent",
]
