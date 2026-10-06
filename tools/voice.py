"""Voice interview, defaults, and flag parsing for the humanizer pipeline.

Pure functions only (no LLM calls) so the orchestrator stays deterministic and
the behaviour is unit-testable.

Interview paths
---------------
A. Inline notes   : message contains a ``VOICE_NOTES:`` block or ``--voice "..."``.
B. Run now (default): pipeline runs with defaults; a Voice Pass menu is appended afterwards.
C. Up-front       : ``--interview`` asks first and pauses (the only blocking path, opt-in).
D. Explicit skip  : ``--no-interview`` / "skip questions" -> defaults, no menu.

The agent never invents personal experiences or numbers. Defaults rely only on what is
in the source text.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from .chunking import default_compression, read_docx, word_count
from .metrics import voice_pattern_metrics

INTERVIEW_QUESTIONS: List[str] = [
    "Name one real project, incident, or number from your work that fits this topic.",
    "What is a mistake or frustration you actually had here? (becomes a candid 'blind spot' sentence)",
    "Any words or phrases you naturally use? (e.g. 'slow down', 'buy-in', 'move fast')",
    "Which sections should stay brief, and which deserve depth?",
    "Register: casual-professional, academic-plain, or formal?",
]

_FLAG_PATTERNS = {
    "interview": re.compile(r"(?<![\w-])--interview\b"),
    "no_interview": re.compile(r"(?<![\w-])--no-interview\b|\bskip (?:the )?(?:questions|interview)\b", re.IGNORECASE),
    "casual_slips": re.compile(r"(?<![\w-])--casual-slips\b"),
    "force_long": re.compile(r"(?<![\w-])--long\b"),
    "force_short": re.compile(r"(?<![\w-])--short\b"),
    "fresh": re.compile(r"(?<![\w-])--fresh\b"),
    "fast": re.compile(r"(?<![\w-])--fast\b|\b(fast|quick(ly)?|rapid(ly)?|speed|express)\b", re.IGNORECASE),
}
_COMPRESS_RE = re.compile(r"(?<![\w-])--compress[= ]+(\d{1,2})%?")
_VOICE_INLINE_RE = re.compile(r"""(?<![\w-])--voice[= ]+(?:"([^"]*)"|'([^']*)')""", re.DOTALL)
_NOTES_BLOCK_RE = re.compile(r"(?:^|\n)\s*VOICE_NOTES:\s*(.*?)(?:\n\s*END_VOICE_NOTES\b|\n\s*\n|\Z)", re.DOTALL | re.IGNORECASE)
_APPLY_RE = re.compile(r"\bapply (?:my )?voice notes\b", re.IGNORECASE)
_SKIP_REPLY_RE = re.compile(r"^\s*(skip|defaults?|use defaults|no thanks|continue)\s*[.!]?\s*$", re.IGNORECASE)
_MIN_WORDS_RE = re.compile(r"\b(?:at least|minimum of|min\.?|no fewer than)\s+(\d[\d,]*)\s+words\b", re.IGNORECASE)
_DIRECTIVE_RE = re.compile(r"\b(humani[sz]e|rewrite|rephrase|make (?:this|it) (?:sound )?(?:more )?human)\b", re.IGNORECASE)


@dataclass
class VoiceRequest:
    source: str = ""
    notes: str = ""
    interview: bool = False
    no_interview: bool = False
    casual_slips: bool = False
    force_mode: Optional[str] = None  # "short" | "long"
    compress: Optional[int] = None
    fresh: bool = False
    fast: bool = False
    apply_notes: bool = False
    skip_reply: bool = False
    min_words: Optional[int] = None


def _load_if_path(candidate: str) -> Optional[str]:
    """If the message is just a path to a .docx/.md/.txt file, return its text."""
    c = candidate.strip().strip('"').strip("'")
    if "\n" in c or len(c) > 260 or not re.search(r"\.(docx|md|txt)$", c, re.IGNORECASE):
        return None
    p = Path(c)
    if not p.is_file():
        return None
    return read_docx(p) if p.suffix.lower() == ".docx" else p.read_text(encoding="utf-8")


def parse_request(user_text: str) -> VoiceRequest:
    """Extract flags, inline voice notes, and the source text from a raw user message."""
    req = VoiceRequest()
    text = user_text

    req.apply_notes = bool(_APPLY_RE.search(text))
    req.skip_reply = bool(_SKIP_REPLY_RE.match(text))
    req.interview = bool(_FLAG_PATTERNS["interview"].search(text))
    req.no_interview = bool(_FLAG_PATTERNS["no_interview"].search(text))
    req.casual_slips = bool(_FLAG_PATTERNS["casual_slips"].search(text))
    req.fresh = bool(_FLAG_PATTERNS["fresh"].search(text))
    req.fast = bool(_FLAG_PATTERNS["fast"].search(text))
    if _FLAG_PATTERNS["force_long"].search(text):
        req.force_mode = "long"
    elif _FLAG_PATTERNS["force_short"].search(text):
        req.force_mode = "short"
    m = _COMPRESS_RE.search(text)
    if m:
        req.compress = max(0, min(60, int(m.group(1))))
    m = _MIN_WORDS_RE.search(text[:600])
    if m:
        req.min_words = int(m.group(1).replace(",", ""))

    notes: List[str] = []
    for m in _VOICE_INLINE_RE.finditer(text):
        notes.append((m.group(1) or m.group(2) or "").strip())
    block = _NOTES_BLOCK_RE.search(text)
    if block:
        notes.append(block.group(1).strip())
    if req.apply_notes:
        # "apply voice notes: <answers>" -> everything after the phrase is the notes
        after = _APPLY_RE.split(text, maxsplit=1)[-1].lstrip(" :\n-")
        if after.strip():
            notes.append(after.strip())
    req.notes = "\n".join(n for n in notes if n)

    # Strip control syntax to get the source document
    src = text
    src = _VOICE_INLINE_RE.sub("", src)
    src = _NOTES_BLOCK_RE.sub("\n", src)
    for pat in _FLAG_PATTERNS.values():
        src = pat.sub("", src)
    src = _COMPRESS_RE.sub("", src)

    # Drop a short leading directive paragraph ("Humanize this essay:") when body follows
    paras = re.split(r"\n\s*\n", src.strip(), maxsplit=1)
    if len(paras) == 2 and len(paras[0].split()) <= 40 and _DIRECTIVE_RE.search(paras[0]) \
            and len(paras[1].split()) > 40:
        src = paras[1]
    src = src.strip()

    loaded = _load_if_path(src)
    req.source = loaded if loaded is not None else src
    return req


def detect_doc_kind(text: str) -> str:
    head = text[:400].lower()
    if re.search(r"^\s*(dear\b|subject:|hi\b|hello\b)", head, re.MULTILINE):
        return "email"
    if re.search(r"\b(memo|memorandum)\b", head):
        return "memo"
    return "assignment"


def resolve_compression(req: VoiceRequest) -> int:
    """Compression target (%) honoring explicit flags and any stated word minimum."""
    words = word_count(req.source)
    target = req.compress if req.compress is not None else default_compression(words, detect_doc_kind(req.source))
    if req.min_words and words:
        headroom = int(max(0.0, (1 - req.min_words / words)) * 100)
        target = min(target, headroom)
    return max(0, target)


def build_voice_profile(req: VoiceRequest, compression: int, refine: bool = False) -> str:
    """Render the VOICE_PROFILE: block consumed by the planner and rewriter."""
    source = "user" if req.notes else "defaults"
    lines = [
        "VOICE_PROFILE:",
        f"source: {source}",
        "register: academic-plain (plain words, hedges like 'I tend to', contractions where natural)",
        f"compression_target: {compression}%" + (" (minimal-edit refinement pass: 0%)" if refine else ""),
        f"casual_slips: {'on (max ~1 per 150 words; list each under SLIPS_USED:)' if req.casual_slips else 'off'}",
    ]
    if req.min_words:
        lines.append(f"min_words: {req.min_words} (compression already capped to respect this)")
    if req.notes:
        lines.append("user_notes (the ONLY personal details you may add; weave in where they fit):")
        lines.extend(f"  {ln}" for ln in req.notes.splitlines())
    else:
        lines.append("user_notes: none. Do NOT invent anecdotes, experiences, names, or numbers; "
                     "use only details already in the source text.")
    lines.extend([
        "defaults: keep existing anecdotes (trim them); allow repeating core terms; vary section shape; "
        "plain 2-4 sentence ending with no quotable closer; ZERO 'not X but Y' pivots; "
        "ZERO colons.",
    ])
    return "\n".join(lines)


def voice_menu() -> str:
    qs = "\n".join(f"{i}. {q}" for i, q in enumerate(INTERVIEW_QUESTIONS, start=1))
    return (
        "OPTIONAL VOICE PASS (skip freely, the draft above is complete):\n"
        "Adding real details is the most effective way to make the text read as yours.\n"
        f"{qs}\n"
        "Reply `apply voice notes:` followed by your answers (any subset) to refine the draft. "
        "Nothing is invented if you skip."
    )


def interview_prompt() -> str:
    qs = "\n".join(f"{i}. {q}" for i, q in enumerate(INTERVIEW_QUESTIONS, start=1))
    return (
        "VOICE_INTERVIEW:\n"
        "Quick questions (one line each, any subset). Reply `skip` to continue with defaults.\n"
        f"{qs}"
    )


def authenticity_slots(sections: List[tuple]) -> List[str]:
    """Labels of sections that read as abstract (little concrete personal detail).

    `sections` is a list of (label, text) pairs for rewritten prose sections.
    """
    out: List[str] = []
    for label, text in sections:
        if word_count(text) < 80:
            continue
        v = voice_pattern_metrics(text)
        if not v["voice_checks_waived"] and v["concreteness_per_100"] < 8.0:
            out.append(label)
    return out
