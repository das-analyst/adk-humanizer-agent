"""Linguistic and AI detection heuristic metrics.

Computes burstiness (sentence length variance), AI cliché density,
sentence opener diversity, readability metrics, and Turnitin / AI detector
risk heuristics (generic adjectives, template openers, unintegrated citations,
and paragraph structure).
"""

from __future__ import annotations

import math
import re
from typing import Any, Dict, List


# 150+ overused AI buzzwords, transitional crutches, and corporate LLM hallmarks
AI_CLICHE_PATTERNS = [
    # Verbs / Actions
    r"\bdelv(e|es|ed|ing)\b",
    r"\btapestr(y|ies)\b",
    r"\bbeacon\b",
    r"\btestament\b",
    r"\bplethora\b",
    r"\bmyriad\b",
    r"\bfoster(s|ed|ing)?\b",
    r"\bpivotal\b",
    r"\bcrucial\b",
    r"\bparamount\b",
    r"\bcornerstone\b",
    r"\bquintessential(ly)?\b",
    r"\bunderpin(s|ned|ning)?\b",
    r"\bharness(es|ed|ing)?\b",
    r"\bunleash(es|ed|ing)?\b",
    r"\bdemystif(y|ies|ied|ying)\b",
    r"\bembark(s|ed|ing)?\b",
    r"\bresonat(e|es|ed|ing)\b",
    r"\bintricac(y|ies)\b",
    r"\bnuance(s)?\b",
    r"\brealm(s)?\b",
    r"\bever[- ]evolving\b",
    r"\blandscape(s)?\b",
    r"\bparadigm(s)?\b",
    r"\btransformative\b",
    r"\bgame[- ]changer\b",
    r"\bmeticulous(ly)?\b",
    r"\bseamless(ly)?\b",
    r"\bholistic(ally)?\b",
    r"\bmultifaceted\b",
    r"\bsynerg(y|ies)\b",
    r"\bspearhead(s|ed|ing)?\b",
    r"\btrailblaz(er|ing)\b",
    r"\bcatalyst\b",
    r"\bindispensable\b",
    r"\bintertwin(e|ed|ing)\b",
    r"\bconduit\b",
    r"\blinchpin\b",
    r"\bvibrant\b",

    # AI Transitional Crutches & Hedging Phrases
    r"\bin conclusion\b",
    r"\bfurthermore\b",
    r"\bmoreover\b",
    r"\badditionally\b",
    r"\bit is (important|crucial|essential|worth noting|worth mentioning|imperative) to (note|mention|remember|highlight|recognize)\b",
    r"\bit should be noted that\b",
    r"\bin today['’]?s (world|digital age|fast[- ]paced world|society)\b",
    r"\bserves? as a (testament|reminder|beacon|catalyst)\b",
    r"\bshed(s|ding)? light on\b",
    r"\bplays? a (crucial|pivotal|vital|key|central) role\b",
    r"\bpaves? the way\b",
    r"\bfirst and foremost\b",
    r"\bby and large\b",
    r"\ba testament to\b",
    r"\brich tapestry\b",
    r"\bdive deep(er)?\b",
    r"\bdeep dive\b",
    r"\bnavigat(e|ing|es) the (complexities|landscape|nuances)\b",
    r"\bunlock(s|ed|ing)? the potential\b",
    r"\bbecome increasingly (evident|important|prevalent)\b",
    r"\ba wide (range|array|variety) of\b",
    r"\bstands? as a\b",
    r"\bnot only .*? but (also)?\b",
    r"\bat its core\b",
    r"\bwith that being said\b",
    r"\bwithout further ado\b",
]

COMPILED_AI_PATTERNS = [re.compile(p, re.IGNORECASE) for p in AI_CLICHE_PATTERNS]

# 10-Point Detector Anti-Pattern Heuristics:
# Generic placeholder adjectives that replace field-specific nouns/verbs
GENERIC_ADJECTIVE_PATTERNS = [
    r"\bsignificant(ly)?\b",
    r"\bimportant(ly)?\b",
    r"\beffective(ly)?\b",
    r"\bessential(ly)?\b",
    r"\bcrucial(ly)?\b",
    r"\bpivotal\b",
    r"\bvital(ly)?\b",
    r"\bnotable\b",
    r"\bmultifaceted\b",
    r"\bcomprehensive(ly)?\b",
    r"\bparamount\b",
    r"\bprofound(ly)?\b",
]
COMPILED_GENERIC_ADJECTIVE_PATTERNS = [re.compile(p, re.IGNORECASE) for p in GENERIC_ADJECTIVE_PATTERNS]

# Template-based impersonal paper openings
TEMPLATE_OPENER_PATTERNS = [
    r"^(this|the present)\s+(paper|essay|study|project|article|analysis|report)\s+(will\s+discuss|aims\s+to|explores|examines|presents|focuses\s+on|investigates)",
    r"^in\s+conclusion[,\s]+(this|the)\s+(paper|essay|study)\s+(has\s+shown|explains|demonstrates|summarizes)",
    r"^the\s+purpose\s+of\s+this\s+(paper|essay|study|project|report)\s+is\s+to\b",
]
COMPILED_TEMPLATE_OPENER_PATTERNS = [re.compile(p, re.IGNORECASE) for p in TEMPLATE_OPENER_PATTERNS]

# Citation pattern: (Author, Year) or (Author et al., Year)
CITATION_REGEX = re.compile(r"\(([A-Z][a-zA-Z\s.-]+?(?:et\s+al\.?|(?:and|&)\s+[A-Z][a-zA-Z\s.-]+?)?,\s*(?:19|20)\d{2}[a-z]?)\)")
SIGNAL_PHRASE_REGEX = re.compile(
    r"\b(according to|demonstrated by|argued by|showed that|as demonstrated|as noted by|revealed that|observed that|found that|reported that|confirm(s|ed|ing)?|suggest(s|ed|ing)?|argues?|contend(s|ed)?|assert(s|ed)?|noted?|highlights?|explains?)\b",
    re.IGNORECASE
)


def split_sentences(text: str) -> List[str]:
    """Split text into sentences while guarding common abbreviations."""
    clean = text.strip()
    if not clean:
        return []

    # Protect common abbreviations and citation tokens
    subs = {
        r"e\.g\.": "e_g_",
        r"i\.e\.": "i_e_",
        r"et\s+al\.": "et_al_",
        r"Dr\.": "Dr_",
        r"Mr\.": "Mr_",
        r"Mrs\.": "Mrs_",
        r"Ms\.": "Ms_",
        r"Prof\.": "Prof_",
        r"vs\.": "vs_",
        r"etc\.": "etc_",
        r"U\.S\.": "U_S_",
    }
    protected = clean
    for pat, rep in subs.items():
        protected = re.sub(pat, rep, protected, flags=re.IGNORECASE)

    raw_sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'“])", protected)
    sentences = []
    for s in raw_sentences:
        s = s.strip()
        if not s:
            continue
        # Restore protected tokens
        for rep, pat in [("e_g_", "e.g."), ("i_e_", "i.e."), ("et_al_", "et al."), ("Dr_", "Dr."), ("Mr_", "Mr."),
                         ("Mrs_", "Mrs."), ("Ms_", "Ms."), ("Prof_", "Prof."), ("vs_", "vs."),
                         ("etc_", "etc."), ("U_S_", "U.S.")]:
            s = s.replace(rep, pat)
        sentences.append(s)
    return sentences


def count_syllables(word: str) -> int:
    """Heuristic syllable counter for Flesch-Kincaid calculation."""
    w = word.lower().strip(".:;?!'\"")
    if len(w) <= 3:
        return 1
    w = re.sub(r"(?:[^laeiouy]|ed|es|e)$", "", w)
    w = re.sub(r"^y", "", w)
    matches = re.findall(r"[aeiouy]{1,2}", w)
    return max(1, len(matches))


def analyze_linguistic_metrics(text: str) -> Dict[str, Any]:
    """Analyze text for burstiness, AI clichés, predictability, readability, and detector risk.

    Returns a structured dictionary with raw metrics, detected markers,
    detector anti-pattern heuristics, and composite Human-Likeness Index (0-100%).
    """
    if not text or not text.strip():
        return {
            "word_count": 0,
            "sentence_count": 0,
            "paragraph_count": 0,
            "burstiness_stdev": 0.0,
            "mean_sentence_length": 0.0,
            "cliche_count": 0,
            "cliches_found": [],
            "generic_adjectives_count": 0,
            "generic_adjectives_found": [],
            "template_openers_found": [],
            "unintegrated_citations_count": 0,
            "unintegrated_citations_found": [],
            "isolated_stub_paragraphs": 0,
            "paragraph_check_waived": True,
            "detector_risk_score": 0.0,
            "flesch_reading_ease": 0.0,
            "flesch_kincaid_grade": 0.0,
            "sentence_opener_diversity": 0.0,
            "human_likeness_index": 50.0,
            "assessment": "No text provided.",
            "sentence_lengths": [],
        }

    sentences = split_sentences(text)
    words = re.findall(r"\b[A-Za-z0-9'’-]+\b", text)
    word_count = len(words)
    sentence_count = len(sentences)

    raw_paragraphs = [p.strip() for p in re.split(r"\n\s*\n+", text.strip()) if p.strip()]
    paragraph_count = max(1, len(raw_paragraphs))

    if sentence_count == 0 or word_count == 0:
        return {
            "word_count": word_count,
            "sentence_count": sentence_count,
            "paragraph_count": paragraph_count,
            "burstiness_stdev": 0.0,
            "mean_sentence_length": 0.0,
            "cliche_count": 0,
            "cliches_found": [],
            "generic_adjectives_count": 0,
            "generic_adjectives_found": [],
            "template_openers_found": [],
            "unintegrated_citations_count": 0,
            "unintegrated_citations_found": [],
            "isolated_stub_paragraphs": 0,
            "paragraph_check_waived": True,
            "detector_risk_score": 0.0,
            "flesch_reading_ease": 0.0,
            "flesch_kincaid_grade": 0.0,
            "sentence_opener_diversity": 0.0,
            "human_likeness_index": 50.0,
            "assessment": "Insufficient text.",
            "sentence_lengths": [],
        }

    # 1. Burstiness (Sentence Length Distribution)
    sentence_lengths = [len(re.findall(r"\b[A-Za-z0-9'’-]+\b", s)) for s in sentences]
    mean_len = sum(sentence_lengths) / sentence_count
    if sentence_count > 1:
        variance = sum((l - mean_len) ** 2 for l in sentence_lengths) / (sentence_count - 1)
        stdev = math.sqrt(variance)
    else:
        stdev = 0.0

    # 2. AI Cliché & Crutch Word Detection
    cliches_found = []
    for pattern in COMPILED_AI_PATTERNS:
        for match in pattern.finditer(text):
            cliches_found.append(match.group(0))

    # 3. Sentence Opener Diversity
    openers = []
    for s in sentences:
        first_word = re.match(r"^[A-Za-z0-9'’-]+", s.strip())
        if first_word:
            openers.append(first_word.group(0).lower())
    unique_openers = len(set(openers))
    opener_diversity = (unique_openers / max(1, len(openers))) * 100.0

    # 4. Turnitin / AI Detector Anti-Pattern Heuristics
    # A. Generic Adjectives
    generic_adjectives_found = []
    for pat in COMPILED_GENERIC_ADJECTIVE_PATTERNS:
        for match in pat.finditer(text):
            generic_adjectives_found.append(match.group(0))

    # B. Template Openers
    template_openers_found = []
    for s in sentences[:3]:  # Check intro sentences
        for pat in COMPILED_TEMPLATE_OPENER_PATTERNS:
            m = pat.search(s.strip())
            if m:
                template_openers_found.append(m.group(0))
    # Also check concluding sentence if text has multiple sentences
    if len(sentences) > 3:
        for pat in COMPILED_TEMPLATE_OPENER_PATTERNS:
            m = pat.search(sentences[-1].strip())
            if m and m.group(0) not in template_openers_found:
                template_openers_found.append(m.group(0))

    # C. Dropped Citations (Citations lacking signal phrases)
    unintegrated_citations_found = []
    for s in sentences:
        citations = CITATION_REGEX.findall(s)
        if citations:
            has_signal = bool(SIGNAL_PHRASE_REGEX.search(s))
            if not has_signal:
                for c in citations:
                    unintegrated_citations_found.append(c)

    # D. Paragraph Cohesion & Graceful Degradation
    # Graceful degradation: for texts under 100 words or bullet-style lists, waive isolated stub check
    paragraph_check_waived = word_count < 100 or any(p.startswith(("-", "*", "•", "1.", "2.")) for p in raw_paragraphs)
    isolated_stub_paragraphs = 0
    if not paragraph_check_waived and paragraph_count > 1:
        for p in raw_paragraphs:
            p_sentences = split_sentences(p)
            p_words = len(re.findall(r"\b[A-Za-z0-9'’-]+\b", p))
            if len(p_sentences) <= 1 and p_words < 35:
                isolated_stub_paragraphs += 1

    # E. Detector Risk Score (0 - 100%)
    risk_points = 0.0
    # Template openers are high risk: 25 pts each
    risk_points += min(50.0, len(template_openers_found) * 25.0)
    # Generic adjectives: 3 pts each up to 25 pts
    risk_points += min(25.0, len(generic_adjectives_found) * 3.0)
    # Monotonous burstiness: if stdev < 5.0, add up to 25 pts
    if stdev < 5.0:
        risk_points += (5.0 - stdev) * 5.0
    # Isolated stub paragraphs (if not waived): 10 pts each
    if not paragraph_check_waived:
        risk_points += min(20.0, isolated_stub_paragraphs * 10.0)
    # Advisory citations: 5 pts each up to 10 pts
    risk_points += min(10.0, len(unintegrated_citations_found) * 5.0)

    detector_risk_score = round(min(100.0, max(0.0, risk_points)), 1)

    # 5. Readability
    total_syllables = sum(count_syllables(w) for w in words)
    words_per_sentence = word_count / max(1, sentence_count)
    syllables_per_word = total_syllables / max(1, word_count)

    flesch_ease = 206.835 - (1.015 * words_per_sentence) - (84.6 * syllables_per_word)
    flesch_ease = max(0.0, min(100.0, round(flesch_ease, 1)))

    fk_grade = (0.39 * words_per_sentence) + (11.8 * syllables_per_word) - 15.59
    fk_grade = max(1.0, min(20.0, round(fk_grade, 1)))

    # 6. Composite Human-Likeness Index (0 - 100%)
    burstiness_score = min(35.0, (stdev / 8.0) * 35.0)
    cliche_penalty = min(40.0, len(cliches_found) * 5.0)
    template_penalty = min(20.0, len(template_openers_found) * 10.0)
    generic_adj_penalty = min(10.0, len(generic_adjectives_found) * 1.5)
    opener_score = min(20.0, (opener_diversity / 100.0) * 20.0)
    length_score = 15.0 if (10 <= mean_len <= 24) else 8.0

    raw_hli = 30.0 + burstiness_score + opener_score + length_score - cliche_penalty - template_penalty - generic_adj_penalty
    hli = max(5.0, min(98.0, round(raw_hli, 1)))

    # Assessment description
    if hli >= 80:
        assessment = "Highly natural and human-like rhythm with varied syntax, authentic voice, and zero/few AI crutches."
    elif hli >= 65:
        assessment = "Moderately natural, but displays slight uniformity or occasional formulaic phrasing."
    elif hli >= 45:
        assessment = "Noticeable AI markers: repetitive sentence lengths, generic adjectives, or frequent transition filler."
    else:
        assessment = "Strong AI signature: high cliché density, template phrasing, uniform cadence, and detector vulnerabilities."

    return {
        "word_count": word_count,
        "sentence_count": sentence_count,
        "paragraph_count": paragraph_count,
        "mean_sentence_length": round(mean_len, 1),
        "burstiness_stdev": round(stdev, 2),
        "sentence_lengths": sentence_lengths,
        "cliche_count": len(cliches_found),
        "cliches_found": cliches_found[:20],
        "generic_adjectives_count": len(generic_adjectives_found),
        "generic_adjectives_found": generic_adjectives_found[:20],
        "template_openers_found": template_openers_found,
        "unintegrated_citations_count": len(unintegrated_citations_found),
        "unintegrated_citations_found": unintegrated_citations_found,
        "isolated_stub_paragraphs": isolated_stub_paragraphs,
        "paragraph_check_waived": paragraph_check_waived,
        "detector_risk_score": detector_risk_score,
        "sentence_opener_diversity": round(opener_diversity, 1),
        "flesch_reading_ease": flesch_ease,
        "flesch_kincaid_grade": fk_grade,
        "human_likeness_index": hli,
        "assessment": assessment,
    }
