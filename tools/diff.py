"""Text diff and delta comparator tool."""

from __future__ import annotations

import difflib
from typing import Any, Dict
from .metrics import analyze_linguistic_metrics
from .chunking import compression_ratio, missing_entities


def compare_texts(original_text: str, humanized_text: str) -> Dict[str, Any]:
    """Compare original and humanized text, analyzing linguistic metric improvements and changes.

    Returns before-and-after metrics, improvements in Human Likeness Index,
    burstiness change, AI detector risk reduction, and citation advisories.
    """
    orig_metrics = analyze_linguistic_metrics(original_text)
    new_metrics = analyze_linguistic_metrics(humanized_text)

    # Word difference
    orig_words = original_text.split()
    new_words = humanized_text.split()
    matcher = difflib.SequenceMatcher(None, orig_words, new_words)
    similarity_ratio = round(matcher.ratio() * 100, 1)

    # Metric changes
    hli_delta = round(new_metrics["human_likeness_index"] - orig_metrics["human_likeness_index"], 1)
    burstiness_delta = round(new_metrics["burstiness_stdev"] - orig_metrics["burstiness_stdev"], 2)
    cliche_reduction = orig_metrics["cliche_count"] - new_metrics["cliche_count"]
    generic_words_reduced = orig_metrics["generic_adjectives_count"] - new_metrics["generic_adjectives_count"]
    detector_risk_delta = round(orig_metrics["detector_risk_score"] - new_metrics["detector_risk_score"], 1)

    # Highlights
    improvements = []
    if hli_delta > 0:
        improvements.append(f"Human-Likeness Index increased by +{hli_delta}% (from {orig_metrics['human_likeness_index']}% to {new_metrics['human_likeness_index']}%)")
    if burstiness_delta > 0:
        improvements.append(f"Sentence burstiness improved by +{burstiness_delta} stdev (more dynamic sentence length cadence)")
    if cliche_reduction > 0:
        improvements.append(f"Eliminated {cliche_reduction} AI cliché(s) / corporate crutch words")
    elif new_metrics["cliche_count"] == 0:
        improvements.append("Zero AI clichés detected in final output")
    if detector_risk_delta > 0:
        improvements.append(f"AI Detector risk reduced by {detector_risk_delta}% (from {orig_metrics['detector_risk_score']}% to {new_metrics['detector_risk_score']}%)")
    if orig_metrics["template_openers_found"] and not new_metrics["template_openers_found"]:
        improvements.append("Eliminated formulaic template paper opening in favor of authentic analytical framing")
    if generic_words_reduced > 0:
        improvements.append(f"Replaced {generic_words_reduced} generic adjective(s) with specific domain phrasing")

    # Citation advisories (Soft recommendation)
    citation_advisories = []
    for cit in new_metrics["unintegrated_citations_found"]:
        author_hint = cit.split(",")[0].strip()
        citation_advisories.append(
            f"Advisory: Citation '({cit})' lacks a signal phrase. Consider introducing it with 'According to {author_hint}...' or 'As {author_hint} demonstrated...' for smoother academic integration."
        )

    # Voice-pattern deltas and material-entity retention (deliberate cuts are not penalized)
    voice_keys = ["colon_density", "contrast_constructions", "tricolon_density", "mic_drop_closers",
                  "pivot_paragraphs", "concreteness_per_100"]
    voice_before = {k: orig_metrics[k] for k in voice_keys}
    voice_after = {k: new_metrics[k] for k in voice_keys}
    miss = missing_entities(original_text, humanized_text)
    material_missing = {k: v for k, v in miss.items() if k in ("citations", "numbers") and v}
    comp = compression_ratio(original_text, humanized_text)

    return {
        "original_metrics": orig_metrics,
        "humanized_metrics": new_metrics,
        "similarity_ratio_pct": similarity_ratio,
        "hli_delta_pct": hli_delta,
        "burstiness_delta": burstiness_delta,
        "cliches_removed": cliche_reduction,
        "remaining_cliches": new_metrics["cliches_found"],
        "generic_words_reduced": generic_words_reduced,
        "detector_risk_delta": detector_risk_delta,
        "citation_advisories": citation_advisories,
        "improvements": improvements,
        "voice_before": voice_before,
        "voice_after": voice_after,
        "compression_pct": comp,
        "missing_material_entities": material_missing,
        "advisory_missing_names": miss.get("names", []),
    }

