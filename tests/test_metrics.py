"""Unit tests for linguistic metrics and diff tools."""

import sys
from pathlib import Path

# Add project root to sys.path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from tools.metrics import analyze_linguistic_metrics, split_sentences
from tools.diff import compare_texts


def test_split_sentences():
    text = "This is a sentence. Here is another one! Is this a third? Yes, e.g. for testing purposes. Also Smith et al. proved this."
    sentences = split_sentences(text)
    assert len(sentences) == 5
    assert "e.g." in sentences[3]
    assert "et al." in sentences[4]


def test_ai_cliche_detection():
    ai_text = (
        "In conclusion, it is important to note that we must delve into the multifaceted realm of AI. "
        "This serves as a testament to the rich tapestry of human innovation. "
        "Furthermore, navigating the landscape fosters pivotal breakthroughs."
    )
    result = analyze_linguistic_metrics(ai_text)
    assert result["cliche_count"] >= 5
    found_lower = [c.lower() for c in result["cliches_found"]]
    assert any("delv" in c for c in found_lower)
    assert any("tapestr" in c for c in found_lower)
    assert result["human_likeness_index"] < 60.0


def test_burstiness_variance():
    # Uniform robotic text: all sentences exactly 7 words
    uniform_text = (
        "Every single sentence has seven words here. "
        "Notice how the rhythm never ever changes. "
        "Uniform sentences create a very robotic feel."
    )
    uniform_res = analyze_linguistic_metrics(uniform_text)

    # Varied human text: 3 words, 22 words, 5 words
    varied_text = (
        "I love this. "
        "Whenever we examine how real people talk, their thoughts expand into long descriptive clauses that wander through vivid ideas, before stopping abruptly. "
        "Short punchy lines work wonders."
    )
    varied_res = analyze_linguistic_metrics(varied_text)

    assert uniform_res["burstiness_stdev"] < 1.0
    assert varied_res["burstiness_stdev"] > 6.0


def test_detector_heuristics():
    # Text with template opener, generic adjectives, and dropped citation
    flagged_text = (
        "This paper will discuss the essential methods for modern cloud computing. "
        "It presents their features, emphasizes their strengths, and explains their benefits. "
        "Significant improvements in performance were reported across effective deployments (Smith, 2023)."
    )
    res = analyze_linguistic_metrics(flagged_text)

    # Template opener detected
    assert len(res["template_openers_found"]) >= 1
    assert "This paper will discuss" in res["template_openers_found"][0]

    # Generic adjectives detected
    assert res["generic_adjectives_count"] >= 2
    found_adj = [a.lower() for a in res["generic_adjectives_found"]]
    assert "essential" in found_adj or "significant" in found_adj or "effective" in found_adj

    # Dropped citation detected (lacks signal phrase)
    assert res["unintegrated_citations_count"] >= 1
    assert any("Smith" in c for c in res["unintegrated_citations_found"])

    # Detector risk score should be elevated
    assert res["detector_risk_score"] > 30.0

    # Short text graceful degradation: under 100 words, paragraph check waived
    assert res["paragraph_check_waived"] is True
    assert res["isolated_stub_paragraphs"] == 0


def test_signal_phrase_citation_integration():
    # Text with integrated signal phrase for citation
    clean_citation_text = (
        "According to Smith (2023), distributed clusters process events with minimal latency. "
        "As recent trials confirm (Johnson et al., 2024), scaling nodes horizontally eliminates bottlenecks."
    )
    res = analyze_linguistic_metrics(clean_citation_text)
    # Should not flag citations when preceded/accompanied by signal phrases
    assert res["unintegrated_citations_count"] == 0


def test_compare_texts_with_detector_deltas():
    original = (
        "This paper will discuss important security strategies. "
        "In conclusion, it is crucial to delve into the rich tapestry of healthcare innovation (Smith, 2023)."
    )
    humanized = (
        "Healthcare systems require rigorous cybersecurity defenses. "
        "According to Smith (2023), hospital networks encounter sophisticated ransomware attempts weekly, "
        "which forces security engineers to isolate legacy diagnostic devices immediately."
    )

    diff = compare_texts(original, humanized)
    assert diff["cliches_removed"] >= 1
    assert diff["detector_risk_delta"] > 0
    assert any("template" in imp.lower() or "detector" in imp.lower() for imp in diff["improvements"])


def test_edge_cases():
    empty_res = analyze_linguistic_metrics("")
    assert empty_res["word_count"] == 0
    assert empty_res["sentence_count"] == 0
    assert empty_res["burstiness_stdev"] == 0.0
    assert empty_res["detector_risk_score"] == 0.0
