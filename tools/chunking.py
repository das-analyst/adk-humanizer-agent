"""Deterministic document tooling for long-form humanization.

Everything here is plain Python (no LLM calls). The orchestrator uses it to:

* decide between the short-form (whole-document) and long-form (section-chunked) pipelines,
* split a document into sections, protecting tables / code / references,
* build a compact digest for the planning phases,
* stitch rewritten sections back together,
* run document-level checks (compression, material-entity retention, voice metrics)
  without sending the full text through a model,
* persist per-section progress so an interrupted run can resume.
"""

from __future__ import annotations

import json
import os
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from xml.etree import ElementTree as ET

from .metrics import analyze_linguistic_metrics, extract_prose, split_sentences

DEFAULT_LONGFORM_WORDS = 1200
DEFAULT_MAX_SECTION_WORDS = 600

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_PASSTHROUGH_HEADING_RE = re.compile(r"^(references|bibliography|works cited|appendix\b.*)$", re.IGNORECASE)
_WORD_RE = re.compile(r"\b[A-Za-z0-9'’-]+\b")


def longform_threshold() -> int:
    """Word threshold at which the section-chunked pipeline takes over (env: LONGFORM_WORDS)."""
    try:
        return int(os.getenv("LONGFORM_WORDS", DEFAULT_LONGFORM_WORDS))
    except ValueError:
        return DEFAULT_LONGFORM_WORDS


def word_count(text: str) -> int:
    return len(_WORD_RE.findall(text))


# ---------------------------------------------------------------------------
# .docx input
# ---------------------------------------------------------------------------
_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def read_docx(path: str | Path) -> str:
    """Convert a .docx file into Markdown-ish text (headings as '#', tables as '|' rows)."""
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read("word/document.xml"))
    body = root.find(f"{_W}body")
    out: List[str] = []

    def para_text(p: ET.Element) -> str:
        return "".join(t.text or "" for t in p.iter(f"{_W}t"))

    def para_level(p: ET.Element) -> int:
        style = p.find(f"{_W}pPr/{_W}pStyle")
        val = style.get(f"{_W}val", "") if style is not None else ""
        m = re.match(r"(?i)heading\s*(\d)", val)
        if m:
            return int(m.group(1))
        return 1 if val.lower() == "title" else 0

    for child in body if body is not None else []:
        if child.tag == f"{_W}p":
            text = para_text(child).strip()
            if not text:
                out.append("")
                continue
            lvl = para_level(child)
            out.append(f"{'#' * lvl} {text}" if lvl else text)
            out.append("")
        elif child.tag == f"{_W}tbl":
            for row in child.iter(f"{_W}tr"):
                cells = ["".join(t.text or "" for t in c.iter(f"{_W}t")).strip() for c in row.iter(f"{_W}tc")]
                out.append("| " + " | ".join(cells) + " |")
            out.append("")
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip() + "\n"


# ---------------------------------------------------------------------------
# Section model
# ---------------------------------------------------------------------------
@dataclass
class Section:
    index: int
    heading: str            # full heading line, e.g. "## Part I" ("" for preamble)
    body: str
    kind: str = "prose"     # "prose" | "passthrough"
    part: int = 1           # >1 when a large section was split further
    parts_total: int = 1
    words: int = 0
    tokens: Dict[str, str] = field(default_factory=dict)  # protected-block placeholders
    title: str = ""         # heading text (kept on continuation parts)

    @property
    def label(self) -> str:
        title = self.title or self.heading.lstrip("# ").strip() or "(preamble)"
        suffix = f" [{self.part}/{self.parts_total}]" if self.parts_total > 1 else ""
        return f"{title}{suffix}"


def _is_block_line(line: str) -> bool:
    s = line.strip()
    return s.startswith("|") or s.startswith("```")


def protect_blocks(body: str) -> Tuple[str, Dict[str, str]]:
    """Replace tables and fenced code with placeholders so the LLM never rewrites them."""
    lines = body.split("\n")
    out: List[str] = []
    store: Dict[str, str] = {}
    buf: List[str] = []
    in_code = False

    def flush() -> None:
        if buf:
            key = f"[[PROTECTED_BLOCK_{len(store) + 1}]]"
            store[key] = "\n".join(buf)
            out.append(key)
            buf.clear()

    for line in lines:
        if line.strip().startswith("```"):
            buf.append(line)
            in_code = not in_code
            if not in_code:
                flush()
            continue
        if in_code or line.strip().startswith("|"):
            buf.append(line)
            continue
        flush()
        out.append(line)
    flush()
    return "\n".join(out), store


def restore_blocks(text: str, store: Dict[str, str]) -> str:
    for key, value in store.items():
        text = text.replace(key, value)
    return text


def parse_sections(text: str, max_section_words: int = DEFAULT_MAX_SECTION_WORDS) -> List[Section]:
    """Split a Markdown document into ordered sections suitable for per-section rewriting."""
    lines = text.split("\n")
    raw: List[Tuple[str, List[str]]] = []
    heading, buf = "", []
    in_code = False
    for line in lines:
        if line.strip().startswith("```"):
            in_code = not in_code
        m = None if in_code else _HEADING_RE.match(line)
        if m and len(m.group(1)) <= 3:
            if heading or "".join(buf).strip():
                raw.append((heading, buf))
            heading, buf = line, []
        else:
            buf.append(line)
    if heading or "".join(buf).strip():
        raw.append((heading, buf))

    sections: List[Section] = []
    for head, body_lines in raw:
        body = "\n".join(body_lines).strip("\n")
        title = head.lstrip("# ").strip()
        masked, store = protect_blocks(body)
        prose_words = word_count(re.sub(r"\[\[PROTECTED_BLOCK_\d+\]\]", " ", masked))
        passthrough = bool(_PASSTHROUGH_HEADING_RE.match(title)) or prose_words < 40
        base = Section(index=0, heading=head, body=body, kind="passthrough" if passthrough else "prose",
                       words=word_count(body), tokens=store, title=title)
        if passthrough:
            sections.append(base)
            continue
        sections.extend(_split_large(base, masked, store, max_section_words))

    for i, s in enumerate(sections):
        s.index = i
    return sections


def _split_large(base: Section, masked: str, store: Dict[str, str], max_words: int) -> List[Section]:
    paras = [p for p in re.split(r"\n\s*\n", masked) if p.strip()]
    chunks: List[List[str]] = [[]]
    count = 0
    for p in paras:
        w = word_count(p)
        if chunks[-1] and count + w > max_words:
            chunks.append([])
            count = 0
        chunks[-1].append(p)
        count += w
    out: List[Section] = []
    for n, chunk in enumerate(chunks, start=1):
        body_masked = "\n\n".join(chunk)
        sub_store = {k: v for k, v in store.items() if k in body_masked}
        out.append(Section(
            index=0, heading=base.heading if n == 1 else "", body=body_masked, kind="prose",
            part=n, parts_total=len(chunks), words=word_count(body_masked), tokens=sub_store,
            title=base.title,
        ))
    return out


def classify_mode(text: str, forced: Optional[str] = None) -> str:
    """Return 'short' or 'long'. `forced` may be 'short' or 'long' (from --short / --long)."""
    if forced in ("short", "long"):
        return forced
    if word_count(text) >= longform_threshold():
        return "long"
    return "long" if len([s for s in parse_sections(text) if s.kind == "prose"]) > 6 else "short"


def default_compression(words: int, doc_kind: str = "assignment") -> int:
    """Default overall compression target (percent) by input size / kind."""
    table = {"assignment": 35, "essay": 35, "memo": 10, "email": 10, "technical": 5, "legal": 0}
    base = table.get(doc_kind, 35)
    if words >= longform_threshold() and doc_kind in ("assignment", "essay"):
        return 35  # long documents: target higher compression to match human style
    return base


# ---------------------------------------------------------------------------
# Digest for the global planning pass
# ---------------------------------------------------------------------------
def build_digest(sections: List[Section]) -> str:
    """Compact outline (headings, sizes, first/last sentences) so planning never sees the full text."""
    rows: List[str] = ["DOCUMENT_DIGEST:"]
    total = sum(s.words for s in sections)
    rows.append(f"total_words: {total}  sections: {len(sections)}")
    for s in sections:
        rows.append(f"\n[{s.index}] {s.label}  ({s.words} words, {s.kind})")
        if s.kind != "prose":
            continue
        sents = split_sentences(re.sub(r"\[\[PROTECTED_BLOCK_\d+\]\]", " ", s.body))
        if sents:
            rows.append(f"  first: {sents[0][:220]}")
            if len(sents) > 1:
                rows.append(f"  last:  {sents[-1][:220]}")
        m = analyze_linguistic_metrics(s.body)
        rows.append(
            f"  metrics: sentences={m['sentence_count']} stdev={m['burstiness_stdev']} "
            f"cliches={m['cliche_count']} colon_density={m['colon_density']} "
            f"contrast={m['contrast_constructions']} tricolon_density={m['tricolon_density']}"
        )
    return "\n".join(rows)


# ---------------------------------------------------------------------------
# Stitching and document-level checks
# ---------------------------------------------------------------------------
def stitch(sections: List[Section], rewritten: Dict[int, str]) -> str:
    """Reassemble the document; sections without a rewrite keep their original text."""
    parts: List[str] = []
    for s in sections:
        body = rewritten.get(s.index)
        if body is None:
            body = restore_blocks(s.body, s.tokens) if s.kind == "prose" else s.body
        else:
            body = restore_blocks(body.strip(), s.tokens)
        block = f"{s.heading}\n\n{body}" if s.heading else body
        parts.append(block.strip("\n"))
    return "\n\n".join(parts).strip() + "\n"


_CITATION_RE = re.compile(r"\(([A-Z][A-Za-z.\s&-]+?(?:et al\.)?,\s*(?:19|20)\d{2}[a-z]?(?:,[^)]*)?)\)")
_NUMBER_RE = re.compile(r"\b\d[\d,]*(?:\.\d+)?%?")
_PROPER_RE = re.compile(r"(?<![.!?]\s)(?<!^)\b([A-Z][a-z]+(?:[ \t]+[A-Z][a-z]+)+)\b")


def material_entities(text: str) -> Dict[str, set]:
    """Names, numbers, and citations that must survive any rewrite (cuts of other content are fine)."""
    prose = extract_prose(text)
    cits = {re.sub(r"\s+", " ", c).replace("&", "and") for c in _CITATION_RE.findall(prose)}
    nums = {n.rstrip(",") for n in _NUMBER_RE.findall(prose) if len(n) > 1 or n in "0123456789"}
    nums = {n for n in nums if not re.fullmatch(r"(19|20)\d{2}", n)}  # years handled via citations
    names = {m.group(1) for m in _PROPER_RE.finditer(prose)}
    return {"citations": cits, "numbers": nums, "names": names}


def missing_entities(original: str, rewritten: str) -> Dict[str, List[str]]:
    """Material entities present in `original` but absent from `rewritten`."""
    o, r = material_entities(original), material_entities(rewritten)
    r_text = rewritten.replace("&", "and")
    missing: Dict[str, List[str]] = {}
    for kind in ("citations", "numbers", "names"):
        gone = []
        for ent in sorted(o[kind]):
            if kind == "citations":
                author = ent.split(",")[0]
                year = re.search(r"(?:19|20)\d{2}", ent)
                ok = ent in r["citations"] or (author.split()[0] in r_text and year and year.group(0) in r_text)
            else:
                ok = ent in r[kind] or ent in r_text
            if not ok:
                gone.append(ent)
        missing[kind] = gone
    return missing


def compression_ratio(original: str, rewritten: str) -> float:
    """Percent of prose words removed (positive = shorter). Tables/references excluded."""
    o, r = word_count(extract_prose(original)), word_count(extract_prose(rewritten))
    return round((1 - r / o) * 100, 1) if o else 0.0


def document_report(original: str, rewritten: str, target_compression: Optional[int] = None) -> Dict[str, Any]:
    """Deterministic whole-document audit used after stitching (no LLM involved)."""
    before, after = analyze_linguistic_metrics(original), analyze_linguistic_metrics(rewritten)
    ratio = compression_ratio(original, rewritten)
    miss = missing_entities(original, rewritten)
    keys = ["human_likeness_index", "detector_risk_score", "burstiness_stdev", "colon_density",
            "contrast_constructions", "tricolon_density", "mic_drop_closers", "pivot_paragraphs",
            "concreteness_per_100", "cliche_count"]
    report: Dict[str, Any] = {
        "before": {k: before[k] for k in keys},
        "after": {k: after[k] for k in keys},
        "compression_pct": ratio,
        "compression_target_pct": target_compression,
        "missing_entities": miss,
    }
    issues: List[str] = []
    if after["contrast_constructions"] > 0:
        issues.append(f"{after['contrast_constructions']} 'not X but Y' constructions remain (max 0)")
    if after["mic_drop_closers"] > 0:
        issues.append(f"{after['mic_drop_closers']} quotable closer phrase(s) remain")
    if after["colon_density"] > 0.0:
        issues.append(f"colon density {after['colon_density']} per 100 words (max 0.0)")
    if after["cliche_count"] > 0:
        issues.append(f"{after['cliche_count']} banned cliché(s) remain")
    if target_compression is not None and abs(ratio - target_compression) > 10:
        issues.append(f"compression {ratio}% is far from target {target_compression}%")
    hard = {k: v for k, v in miss.items() if k in ("citations", "numbers") and v}
    if hard:
        issues.append("missing material entities: " + "; ".join(f"{k}={v}" for k, v in hard.items()))
    report["advisory_missing_names"] = miss.get("names", [])
    report["issues"] = issues
    report["passed"] = not issues
    return report


# ---------------------------------------------------------------------------
# Post-Processing Sanitizers
# ---------------------------------------------------------------------------
def sanitize_markdown(text: str) -> str:
    """Strip markdown formatting (bold, italics, headers) from text while preserving protected blocks."""
    masked, store = protect_blocks(text)
    
    # Remove headers: ^#+ 
    masked = re.sub(r"^#{1,6}\s+(.*?)$", r"\1", masked, flags=re.MULTILINE)
    
    # Remove bold: **text** or __text__
    masked = re.sub(r"\*\*(.*?)\*\*", r"\1", masked)
    masked = re.sub(r"__(.*?)__", r"\1", masked)
    
    # Remove italics: *text* or _text_
    masked = re.sub(r"(?<!\S)\*(.*?)\*(?!\S)", r"\1", masked)
    masked = re.sub(r"(?<!\S)_(.*?)_(?!\S)", r"\1", masked)
    
    # Remove dangling standalone '**' or '###' that Qwen sometimes outputs
    masked = re.sub(r"^\s*\*\*\s*$", "", masked, flags=re.MULTILINE)
    masked = re.sub(r"^\s*###+\s*$", "", masked, flags=re.MULTILINE)
    
    return restore_blocks(masked.strip(), store)


def sanitize_punctuation(text: str) -> str:
    """Replace colons and rigid pivots in prose."""
    masked, store = protect_blocks(text)
    
    # Replace colons followed by a space with a comma
    masked = re.sub(r":\s+", ", ", masked)
    
    # Identify and flatten 'However,'
    masked = re.sub(r"^\s*However,\s*", "", masked, flags=re.IGNORECASE | re.MULTILINE)
    masked = re.sub(r"(?<=\.\s)However,\s*", "", masked, flags=re.IGNORECASE)
    
    return restore_blocks(masked.strip(), store)


# ---------------------------------------------------------------------------
# Resume support
# ---------------------------------------------------------------------------
def progress_path(run_id: str, root: Optional[Path] = None) -> Path:
    base = root or Path(__file__).resolve().parent.parent / ".humanizer_runs"
    base.mkdir(parents=True, exist_ok=True)
    return base / f"{re.sub(r'[^A-Za-z0-9_.-]', '_', run_id)}.json"


def save_progress(run_id: str, data: Dict[str, Any], root: Optional[Path] = None) -> None:
    progress_path(run_id, root).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_progress(run_id: str, root: Optional[Path] = None) -> Dict[str, Any]:
    p = progress_path(run_id, root)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

