"""Lead Orchestrator for AI Text Humanization Architecture.

Coordinates specialist subagents through a disciplined 4-phase transformation
pipeline: Diagnostic Telemetry, Cadence Blueprinting, Deep Prose Rewriting,
and Quality Gate Auditing.

Supports dual-mode execution:
- Mode 1 (Full Pipeline Workflow): Runs Phase 1 -> Phase 2 -> Phase 3 -> Phase 4
  automatically with a score-gated retry loop until target metrics are achieved.
- Mode 2 (Single Specialist Routing): Directly routes to an individual specialist
  when the user requests targeted analysis or drafting.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import AsyncGenerator, Optional

# Ensure project root is in sys.path
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.adk.utils.context_utils import Aclosing

# Robust sibling import fallback: works both when started from root and within package
try:
    from diagnostic_agent.agent import root_agent as diagnostic_agent
    from style_planner.agent import root_agent as style_planner_agent
    from rewriter_agent.agent import root_agent as rewriter_agent
    from critic_agent.agent import root_agent as critic_agent
except ImportError:
    from agents.diagnostic_agent.agent import root_agent as diagnostic_agent
    from agents.style_planner.agent import root_agent as style_planner_agent
    from agents.rewriter_agent.agent import root_agent as rewriter_agent
    from agents.critic_agent.agent import root_agent as critic_agent


class HumanizerOrchestrator(BaseAgent):
    """Lead Workflow & Intent-Aware Orchestrator for AI Text Humanization."""

    max_retries: int = 2

    def _extract_user_prompt(self, ctx: InvocationContext) -> str:
        """Extract the text from the latest user message."""
        parts: list[str] = []
        if ctx.user_content and ctx.user_content.parts:
            for p in ctx.user_content.parts:
                if hasattr(p, "text") and p.text:
                    parts.append(p.text)
        if not parts and ctx.session and ctx.session.events:
            for ev in reversed(ctx.session.events):
                if ev.author == "user" and ev.content and ev.content.parts:
                    for p in ev.content.parts:
                        if hasattr(p, "text") and p.text:
                            parts.append(p.text)
                    if parts:
                        break
        return " ".join(parts).strip()

    def _detect_target_agent(self, user_text: str) -> Optional[BaseAgent]:
        """Detect if user is targeting a single specialist.

        Returns the specific BaseAgent if targeted, or None for the full pipeline.
        Scopes detection strictly to the directive preamble to prevent body text keywords
        (e.g., 'diagnostic', 'metrics', 'audit') from hijacking the pipeline.
        """
        text_lower = user_text.lower().strip()

        # Inspect only the initial directive / preamble before double newlines or within first 250 chars
        directive = text_lower[:250].split("\n\n")[0]

        # Phase 3: Rewriter keywords in directive
        if any(re.search(pat, directive) for pat in [
            r"\b(just|only)\s+rewrite\b",
            r"\brewrite\s+only\b",
            r"\brun\s+(the\s+)?rewriter\b",
            r"\b(draft|rewrite)\s+only\b",
            r"\bgenerate\s+draft\s+only\b",
            r"--rewrite-only\b",
        ]):
            return self.sub_agents[2]  # rewriter_agent

        # Phase 4: Critic / Audit keywords in directive
        if any(re.search(pat, directive) for pat in [
            r"\b(just|only)\s+(audit|critic|scorecard)\b",
            r"\b(audit|critic|scorecard)\s+only\b",
            r"\brun\s+(the\s+)?critic\b",
            r"\bverify\s+fidelity\b",
            r"--(critic|audit)-only\b",
        ]):
            return self.sub_agents[3]  # critic_agent

        # Phase 1: Diagnostic keywords in directive
        if any(re.search(pat, directive) for pat in [
            r"\bdiagnos(e|is|tic)\b",
            r"\bcheck\s+(for\s+)?(burstiness|clich[eé]s?|metrics?)\b",
            r"\bclich[eé]\s+scan\b",
            r"\b(turnitin|detector|detection)\s*(check|scan|risk)?\b",
            r"--diagnostic\b",
        ]):
            return self.sub_agents[0]  # diagnostic_agent

        # Phase 2: Blueprint / Style Planner keywords in directive
        if any(re.search(pat, directive) for pat in [
            r"\bblueprint\b",
            r"\bstyle\s+(plan|planner)\b",
            r"\bcadence\s+plan\b",
            r"--blueprint\b",
        ]):
            return self.sub_agents[1]  # style_planner_agent

        return None

    def _is_fast_track(self, user_text: str) -> bool:
        """Detect if user is requesting fast-track execution (skip diagnostic & blueprint phases)."""
        text = user_text.lower()
        return any(re.search(pat, text) for pat in [
            r"\b(fast|quick(ly)?|rapid(ly)?|speed|express)\b",
            r"--fast\b",
        ])

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        if not self.sub_agents:
            return

        user_text = self._extract_user_prompt(ctx)
        target_agent = self._detect_target_agent(user_text)

        # ------------------------------------------------------------------
        # MODE 2: Single Specialist Execution
        # ------------------------------------------------------------------
        if target_agent is not None:
            async with Aclosing(target_agent.run_async(ctx)) as agen:
                async for event in agen:
                    yield event
            return

        # ------------------------------------------------------------------
        # MODE 1: Pipeline Workflow with Quality Score Gate Loop
        # ------------------------------------------------------------------
        diag_agent = self.sub_agents[0]
        style_agent = self.sub_agents[1]
        rewrite_agent = self.sub_agents[2]
        critic_agent = self.sub_agents[3]

        is_fast_track = self._is_fast_track(user_text)

        # Standard Pipeline: Run Phase 1 (Diagnostics) & Phase 2 (Blueprint)
        if not is_fast_track:
            # Phase 1: Linguistic Diagnostics
            async with Aclosing(diag_agent.run_async(ctx)) as agen:
                async for event in agen:
                    yield event
                    if ctx.should_pause_invocation(event):
                        return

            # Phase 2: Cadence & Style Blueprint
            async with Aclosing(style_agent.run_async(ctx)) as agen:
                async for event in agen:
                    yield event
                    if ctx.should_pause_invocation(event):
                        return

        # Phases 3 & 4: Deep Rewriting + Quality Gate Audit Loop
        for attempt in range(self.max_retries + 1):
            # Phase 3: Rewriter
            async with Aclosing(rewrite_agent.run_async(ctx)) as agen:
                async for event in agen:
                    yield event
                    if ctx.should_pause_invocation(event):
                        return

            # Phase 4: Critic Audit
            critic_text_parts: list[str] = []
            async with Aclosing(critic_agent.run_async(ctx)) as agen:
                async for event in agen:
                    yield event
                    if event.content and event.content.parts:
                        for p in event.content.parts:
                            if hasattr(p, "text") and p.text:
                                critic_text_parts.append(p.text)
                    if ctx.should_pause_invocation(event):
                        return

            full_critic_text = " ".join(critic_text_parts)

            # Quality Score Gate Check
            is_approved = (
                "APPROVED" in full_critic_text
                and "REVISE_REQUIRED" not in full_critic_text
            )

            # Pass quality gate or reached maximum retry budget
            if is_approved or attempt >= self.max_retries:
                break

    async def _run_live_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        raise NotImplementedError("Live audio/video streaming is not supported.")
        yield


root_agent = HumanizerOrchestrator(
    name="humanizer_orchestrator",
    description=(
        "Lead Orchestrator that sequences specialist subagents through a "
        "disciplined 4-phase humanization pipeline: Diagnostic Telemetry, "
        "Syntactic Blueprinting, Deep Prose Rewriting, and Fidelity Auditing. "
        "Supports automated full-pipeline execution with a quality score gate, "
        "as well as targeted single-specialist routing."
    ),
    sub_agents=[
        diagnostic_agent,
        style_planner_agent,
        rewriter_agent,
        critic_agent,
    ],
)
