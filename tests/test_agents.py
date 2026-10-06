"""Unit tests for multi-agent architecture, skills loading, and dual-mode routing."""

import os
import sys
from pathlib import Path

# Add project root to sys.path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))


def test_skills_exist_and_populated():
    skills_dir = _root / "skills"
    assert skills_dir.exists(), "skills directory must exist"

    expected_skills = [
        "human-cadence-standard",
        "anti-ai-cliche-lexicon",
        "tone-rubrics",
        "academic-detector-rubrics",
    ]

    for skill in expected_skills:
        skill_file = skills_dir / skill / "SKILL.md"
        assert skill_file.exists(), f"Skill file {skill_file} must exist"
        content = skill_file.read_text(encoding="utf-8")
        assert len(content) > 100, f"Skill file {skill_file} should not be empty"


def test_subagents_loaded():
    from agents.diagnostic_agent.agent import root_agent as diagnostic
    from agents.style_planner.agent import root_agent as style_planner
    from agents.rewriter_agent.agent import root_agent as rewriter
    from agents.critic_agent.agent import root_agent as critic

    assert diagnostic.name == "diagnostic_agent"
    assert style_planner.name == "style_planner"
    assert rewriter.name == "rewriter_agent"
    assert critic.name == "critic_agent"

    # Verify diagnostic and critic have tools
    assert len(diagnostic.tools) >= 1
    assert len(critic.tools) >= 1


def test_orchestrator_subagents_registered():
    from agents.humanizer_orchestrator.agent import root_agent as orchestrator

    assert orchestrator.name == "humanizer_orchestrator"
    subagent_names = [sa.name for sa in orchestrator.sub_agents]
    assert "diagnostic_agent" in subagent_names
    assert "style_planner" in subagent_names
    assert "rewriter_agent" in subagent_names
    assert "critic_agent" in subagent_names
    assert len(orchestrator.sub_agents) == 4


def test_orchestrator_intent_routing():
    from agents.humanizer_orchestrator.agent import root_agent as orchestrator

    # Mode 2: Targeted specialist intents
    assert orchestrator._detect_target_agent("Please run diagnostic on this text").name == "diagnostic_agent"
    assert orchestrator._detect_target_agent("Just diagnose this paragraph").name == "diagnostic_agent"
    assert orchestrator._detect_target_agent("Check for cliches in this article").name == "diagnostic_agent"
    assert orchestrator._detect_target_agent("Run a Turnitin scan on this draft").name == "diagnostic_agent"
    assert orchestrator._detect_target_agent("Detector check please").name == "diagnostic_agent"

    assert orchestrator._detect_target_agent("Show me the blueprint only").name == "style_planner"
    assert orchestrator._detect_target_agent("Just create a style plan").name == "style_planner"

    assert orchestrator._detect_target_agent("Please rewrite only").name == "rewriter_agent"
    assert orchestrator._detect_target_agent("Just rewrite this draft").name == "rewriter_agent"

    assert orchestrator._detect_target_agent("Just audit this rewrite").name == "critic_agent"
    assert orchestrator._detect_target_agent("Critic only please").name == "critic_agent"

    # Mode 1: Full pipeline defaults (raw text or full humanize request)
    assert orchestrator._detect_target_agent("Humanize this text please.") is None
    assert orchestrator._detect_target_agent(
        "In today's digital age, navigating the tapestry of technology is crucial."
    ) is None

    # Regression test: Long-form text with keywords inside body text must not hijack pipeline
    long_essay_with_keywords = (
        "Let's rewrite this content in human voice:\n\n"
        "# Executive Leadership Plan\n"
        "In this paper, we conduct a diagnostic analysis of clinical data systems. "
        "We also execute an audit of data governance and create a blueprint for development."
    )
    assert orchestrator._detect_target_agent(long_essay_with_keywords) is None


def test_model_config_resolution():
    from config import get_configured_model

    # Test NVIDIA NIM resolution
    os.environ["HUMANIZER_ANALYTIC_MODEL"] = "nvidia_nim/google/gemma-4-31b-it"
    model = get_configured_model()
    assert "openai/google/gemma-4-31b-it" in model.model

    # Test OpenRouter resolution
    os.environ["HUMANIZER_ANALYTIC_MODEL"] = "openrouter/nvidia/nemotron-3.5-lightning:free"
    model_or = get_configured_model()
    assert model_or.model == "openrouter/nvidia/nemotron-3.5-lightning:free"

    # Test Local Ollama resolution
    os.environ["HUMANIZER_ANALYTIC_MODEL"] = "ollama/qwen2.5:7b"
    model_ol = get_configured_model()
    assert model_ol.model == "openai/qwen2.5:7b"


def test_mcp_server_registered():
    from mcp_servers.linguistic_tools.server import mcp

    assert mcp.name == "linguistic-tools-server"


def test_orchestrator_fast_track_detection():
    from tools.voice import parse_request

    assert parse_request("Quickly humanize this draft").fast is True
    assert parse_request("Fast rewrite: In today's world...").fast is True
    assert parse_request("Speed mode humanization").fast is True
    assert parse_request("Humanize this with --fast flag").fast is True
    assert parse_request("Standard humanize of this text").fast is False
    assert parse_request("Please humanize this text in a natural tone.").fast is False


def test_critic_agent_tools_streamlined():
    from agents.critic_agent.agent import root_agent as critic

    assert len(critic.tools) == 1
    assert critic.tools[0].__name__ == "compare_texts"
    assert "Adaptive Gatekeeping" in critic.instruction
    assert "Revision Directives:" in critic.instruction
    assert "Turnitin" in critic.instruction or "Detector" in critic.instruction
    assert "Advisory Notes" in critic.instruction


def test_rewriter_revision_instructions():
    from agents.rewriter_agent.agent import root_agent as rewriter

    assert "Revision Protocol" in rewriter.instruction
    assert "Zero Banned Words & Self-Audit" in rewriter.instruction
    assert "Material Fact Preservation (Zero Fabrication)" in rewriter.instruction
    assert "Zero Template Openers" in rewriter.instruction or "template" in rewriter.instruction.lower()
