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
from typing import AsyncGenerator, Optional, Dict, Any, List
import json

# Ensure project root is in sys.path
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.adk.utils.context_utils import Aclosing
from google.adk.runners import InMemoryRunner
from google.genai import types

def text_event(text: str, author: str = "assistant") -> Event:
    """Create an ADK Event properly packaging text into Content parts."""
    return Event(
        author=author,
        content=types.Content(role=author, parts=[types.Part.from_text(text=text)])
    )

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

from tools.voice import parse_request, resolve_compression, build_voice_profile, voice_menu, interview_prompt
from tools.chunking import parse_sections, build_digest, stitch, document_report, classify_mode, sanitize_markdown, sanitize_punctuation, word_count

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

    def _get_history_source(self, ctx: InvocationContext) -> Optional[str]:
        if not ctx.session or not ctx.session.events:
            return None
        for ev in reversed(ctx.session.events):
            if ev.author == "user" and ev.content and ev.content.parts:
                for p in ev.content.parts:
                    if hasattr(p, "text") and p.text and len(p.text) > 50:
                        return p.text
        return None

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
        # MODE 1: Pipeline Workflow
        # ------------------------------------------------------------------
        req = parse_request(user_text)

        if req.interview:
            yield text_event(interview_prompt())
            return
            
        source = req.source
        if not source:
            source = self._get_history_source(ctx)
        if not source:
            yield text_event("Please provide the text you would like to humanize.")
            return

        compression = resolve_compression(req)
        voice_profile = build_voice_profile(req, compression, refine=req.apply_notes)
        mode = classify_mode(source, req.force_mode)

        if mode == "short":
            async for ev in self._run_short_mode(ctx, req, source, voice_profile):
                yield ev
        else:
            async for ev in self._run_long_mode(ctx, req, source, voice_profile, compression):
                yield ev

        if not req.no_interview and not req.apply_notes and not req.skip_reply:
            yield text_event("\n---\n" + voice_menu())

    async def _run_isolated(self, agent, prompt: str) -> AsyncGenerator[Event, None]:
        from google.adk.runners import Runner
        from google.adk.sessions.in_memory_session_service import InMemorySessionService
        from google.genai import types
        import uuid
        
        runner = Runner(
            agent=agent,
            app_name=self.name,
            session_service=InMemorySessionService(),
            auto_create_session=True
        )
        msg = types.Content(role='user', parts=[types.Part.from_text(text=prompt)])
        session_id = str(uuid.uuid4())
        async for ev in runner.run_async(user_id='orchestrator', session_id=session_id, new_message=msg):
            yield ev

    async def _run_short_mode(
        self, ctx: InvocationContext, req, source: str, voice_profile: str
    ) -> AsyncGenerator[Event, None]:
        diag_agent, style_agent, rewrite_agent, critic_agent = self.sub_agents

        
        if not req.fast and not req.apply_notes:
            async for ev in self._run_isolated(diag_agent, source):
                yield ev
            async for ev in self._run_isolated(style_agent, f"{source}\n\n{voice_profile}"):
                yield ev

        for attempt in range(self.max_retries + 1):
            async for ev in self._run_isolated(rewrite_agent, f"{source}\n\n{voice_profile}"):
                yield ev

            critic_text_parts = []
            async for ev in self._run_isolated(critic_agent, f"{source}"):
                if ev.content and ev.content.parts:
                    for p in ev.content.parts:
                        if hasattr(p, "text") and p.text:
                            critic_text_parts.append(p.text)
                yield ev

            full_critic_text = " ".join(critic_text_parts)
            if "APPROVED" in full_critic_text and "REVISE_REQUIRED" not in full_critic_text:
                break

    async def _run_long_mode(
        self, ctx: InvocationContext, req, source: str, voice_profile: str, compression: int
    ) -> AsyncGenerator[Event, None]:
        diag_agent, style_agent, rewrite_agent, critic_agent = self.sub_agents
        
        sections = parse_sections(source)
        digest = build_digest(sections)

        yield text_event(f"**Long-form Mode**: Chunked into {len(sections)} sections. Building global plan...\n")

        if not req.fast and not req.apply_notes:
            async for ev in self._run_isolated(style_agent, f"{digest}\n\n{voice_profile}"):
                if ev.content and ev.content.parts:
                    for p in ev.content.parts:
                        if hasattr(p, "text") and p.text:
                            yield text_event(f"**Style Plan**:\n```\n{p.text[:300]}...\n```\n")

        import asyncio
        
        sem = asyncio.Semaphore(2)  # Map-reduce concurrency set to 2 for safe memory execution

        async def _process_section(s):
            async with sem:
                if s.kind != "prose":
                    return s.index, s.body
                    
                draft_parts = []
                prompt = (
                    "SECTION_INPUT:\n"
                    "SECTION_TEXT:\n"
                    f"{s.body}\n\n"
                    f"{voice_profile}"
                )
                async for ev in self._run_isolated(rewrite_agent, prompt):
                    if ev.content and ev.content.parts:
                        for p in ev.content.parts:
                            if hasattr(p, "text") and p.text:
                                draft_parts.append(p.text)
                
                draft = " ".join(draft_parts)
                if "HUMANIZED_DRAFT:" in draft:
                    draft = draft.split("HUMANIZED_DRAFT:")[-1].strip()
                if "SLIPS_USED:" in draft:
                    draft = draft.split("SLIPS_USED:")[0].strip()
                    
                draft = sanitize_markdown(draft)
                draft = sanitize_punctuation(draft)
                
                # Compression check & second pass
                target_words = int(s.words * (1 - compression / 100))
                if word_count(draft) > target_words * 1.15:  # 15% buffer
                    trim_prompt = (
                        f"Shorten the following text to exactly {target_words} words. "
                        "Delete filler, adjectives, and wrap-up sentences. Output ONLY plain text with NO markdown formatting.\n\n"
                        f"{draft}"
                    )
                    trim_parts = []
                    async for ev in self._run_isolated(rewrite_agent, trim_prompt):
                        if ev.content and ev.content.parts:
                            for p in ev.content.parts:
                                if hasattr(p, "text") and p.text:
                                    trim_parts.append(p.text)
                    
                    trimmed_draft = " ".join(trim_parts)
                    if "HUMANIZED_DRAFT:" in trimmed_draft:
                        trimmed_draft = trimmed_draft.split("HUMANIZED_DRAFT:")[-1].strip()
                    if "SLIPS_USED:" in trimmed_draft:
                        trimmed_draft = trimmed_draft.split("SLIPS_USED:")[0].strip()
                    
                    draft = sanitize_markdown(trimmed_draft)
                    draft = sanitize_punctuation(draft)
                
                return s.index, draft.strip()

        yield text_event("* Rewriting all sections concurrently with self-auditing...\n")
        
        results = await asyncio.gather(*[_process_section(s) for s in sections])
        rewritten = {idx: draft for idx, draft in results}

        yield text_event("* Stitching sections & running document audit...\n")
        final_doc = stitch(sections, rewritten)
        report = document_report(source, final_doc, compression)
        
        yield text_event(f"**Document Audit Result**:\n```json\n{json.dumps(report, indent=2)}\n```\n")
        
        verdict = "APPROVED" if report.get("passed") else f"APPROVED (Advisories: {'; '.join(report.get('issues', []))})"
        yield text_event(f"\nCRITIC_VERDICT:\n{verdict}\n\nApproved Humanized Output:\n{final_doc}")

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
