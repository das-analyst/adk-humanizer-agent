# Human Voice Patterns Standard

Detectors do not mainly flag short sentences or fancy words. They flag **polished symmetry**: every section built the same way, every idea resolved neatly, nothing specific, nothing awkward. This skill describes how a real person writes the same material. It is derived from a controlled comparison: an AI draft versus the same assignment rewritten by hand by its author. The hand-written version was not flagged. Sentence-length variance was almost identical in both, so **burstiness is secondary**. What differed is below.

---

## 1. The Seven Differences

### 1. Specific over general
AI prose says what is *generally true*. A person says what *happened to them*. Replace general claims with a concrete detail from the source or from the Voice Profile.
- AI: *"Technical specialists often assume analytical rigor automatically commands influence."*
- Human: *"I can build predictive models, but if the nurses can't read the results or don't trust the motive, my work has close to zero value."*

> **Never invent** experiences, numbers, names, or employers. Use only what is in the source text or the `VOICE_PROFILE:`. If a section has no concrete detail, leave it plain and list it under *Authenticity Slots*.

### 2. Cut, don't polish
People leave things out. Apply the `compression_target` from the blueprint:
- Delete sentences that restate the previous one ("Persuasion without documented process creates short-term buy-in but leaves long-term vulnerability.").
- Delete wrap-up sentences that moralize a paragraph.
- Delete a sub-point when two sub-points say the same thing.
- Keep every number, name, and citation the argument depends on.

### 3. Uneven sections
Do **not** give every section the same shape (*strength → anecdote → "However…" → lesson*). Vary on purpose:
- one section is three sentences, another is a long paragraph;
- one opens with a claim, another with an example, another with a citation;
- one has no tidy ending.

### 4. Plain, spoken-register words
| Avoid | Prefer |
|---|---|
| temper urgency with deliberate consensus | slow down and check with people first |
| intellectual bottleneck | everything goes through a few people |
| illuminates / underscores | shows |
| relinquish unilateral control | let go of control |
| a distinct behavioral pattern | I tend to |
| fundamentally transform | change |
| extraordinary heights | (cut it) |

### 5. Few colons, few contrasts
These are the most reliable AI signatures:
- `X is not Y: it is Z` / `not merely X but Y` / `not about X; it is about Y` → **at most one per document**; say the positive claim directly.
- Colons in running prose → **at most ~1 per 100 words**. Prefer a comma or a new sentence.
- Three-item lists ("shared power, cultivating autonomy, and building self-efficacy") → use two items, or four, or a plain sentence. Do not default to three.

### 6. Hedged, first-person judgment
People say *"I tend to"*, *"I need to"*, *"might"*, *"I've noticed"*, *"in my experience"*. AI states conclusions as certainties. Use hedges where the source is a personal reflection, and plain assertions where it is a fact.

### 7. Quiet endings
End paragraphs and the document without a quotable line. Two to four plain sentences saying what the author will do or what they learned. Never end on a "what no one could achieve alone" sentence.

---

## 2. Vocabulary: allow repetition
LLMs rotate synonyms to avoid repeating a word. People keep saying "governance" or "technical solution" because that is the term they use. **Do not substitute synonyms for core terms.** Repeating a key noun three times in a paragraph is natural.

---

## 3. Paragraph Openers
Do not open consecutive paragraphs with a contrast pivot ("However…", "Yet…", "Nevertheless…", "Where my X is tested…"). Allow **at most one** pivot opener per 800 words. Rotate openers with plain starts: a claim, an example, a citation, a short question.

---

## 4. Citations
Keep every citation. Mix the forms: *"Edmondson (2018) argues…"*, *"…(Bandura, 1997)."*, *"Kouzes and Posner (2023, Chapter 9) state…"*. Do not force a signal phrase onto every citation; a human leaves some bare.

---

## 5. Casual-Slips Mode (opt-in: `--casual-slips`)
Off by default. When the user turns it on, allow **loosely written but still correct** prose:
- a sentence starting with *And* or *But*;
- one comma-light, slightly run-on sentence now and then;
- an informal clause ("pretty fast", "move things around");
- a contraction in formal prose.

Limits: no more than about **1 slip per 150 words**. **Never** introduce spelling errors, grammar that changes meaning, wrong facts, or broken citations. After the draft, list where slips were used under *Slips Used*, so the author can revert any.

---

## 6. Before / After (from the reference pair)

> **AI draft:** "That assumption fails in practice. A sophisticated predictive model or statistical pipeline creates zero organizational value if frontline clinicians, analysts, and executive stakeholders distrust its motives or feel sidelined by its implementation."
>
> **Human rewrite:** "As a technical expert, I can build predictive models or statistical test pipelines, but if the frontline clinicians and nurses don't find it easy to interpret the results and don't trust the motives behind such sophisticated implementations, then my efforts would result in minimal to zero organizational value."

> **AI draft (conclusion):** "…the most critical leadership differentiator is profoundly human: the ability to listen with humility, foster genuine psychological safety, and enable multidisciplinary teams to achieve together what no individual could ever achieve alone."
>
> **Human rewrite:** "Technical depth along with elevating the capacity, confidence, and voice of those around you helps us grow into an effective leader."

> **AI draft (collaboration, ~120 words):** four sentences of anecdote about sprint planning, embedded nurse specialists, and mutual vulnerability, then a lesson.
>
> **Human rewrite (~45 words):** "My collaboration approach has historically relied on goodwill rather than systematic structures. But these informal relationships often remain fragile. I should dismantle traditional operational walls, let others peep in, and constantly seek inputs from others."

---

## 7. Self-Check Before Delivering
1. Does every section differ in shape and length from its neighbors?
2. Is there at most one "not X but Y" and about one colon per 100 words?
3. Is there a quotable closing line anywhere? Remove it.
4. Is the document shorter by the compression target, with every number, name, and citation still present?
5. Does any paragraph make a claim with no concrete detail? Cut it, shorten it, or list it as an Authenticity Slot.
6. Were any facts, experiences, or numbers added that are not in the source or Voice Profile? Remove them.
