# Human Cadence & Syntactic Rhythm Standard

This skill establishes the syntactic and rhythmic architecture for authentic human writing, combating the mechanical monotony typical of Large Language Models.

---

## 1. The Principle of Burstiness (Sentence Length Variance)

Large Language Models generate text with uniform sentence lengths (typically clustering tightly around 15–20 words with standard deviation < 5.0). Human writing breathes, accelerates, pauses, and surges.

### Target Distribution (Advisory)
- **Overall Standard Deviation:** Aim for roughly **8.0 or higher**; this is a soft check, not a gate. Do not distort sentences to hit it.
- **Micro-Sentences (3–8 words):** ~10–20% of text, used where the thought is short.
- **Medium Sentences (12–18 words):** the bulk of linear narrative.
- **Complex Sentences (22–35 words):** where the idea genuinely needs layers.

### Cadence Pattern Examples
> **Robotic Uniformity (Negative Pattern):**
> "The implementation of artificial intelligence in healthcare has revolutionized patient diagnostics. Medical professionals can now analyze radiological imagery with unprecedented speed. Furthermore, administrative workflows have been significantly streamlined across hospital systems. This transition represents a major milestone in modern clinical care." *(Sentence lengths: 10, 11, 10, 10 — Stdev: 0.5)*

> **Human Cadence (Positive Pattern):**
> "AI changed hospital diagnostics almost overnight. Radiologists who once spent hours squinting at inconclusive scans now get instant second opinions from neural networks trained on millions of clinical records. The paperwork shrank, too. It wasn't seamless, but the payoff arrived faster than anyone predicted." *(Sentence lengths: 6, 23, 4, 11 — Stdev: 7.6)*

---

## 2. Anti-Monotony Guardrails (Advisory)

> Cadence is **secondary**. A hand-written paper that passed detection and the flagged AI draft had nearly identical sentence-length variance (stdev 8.6 vs 7.8). Do not force a rhythm formula; forced patterns (a short punch sentence in every paragraph, rigid length quotas) are themselves recognizable. Prioritize `human-voice-patterns/SKILL.md`.

1. **Avoid runs of identical length:** do not let five or more consecutive sentences sit within 2 words of one another.
2. **Short sentences are optional.** Use them where the thought is short, not by quota.
3. **Intentional fragments:** allowed when natural.
4. **Punctuation diversity:**
   - Use em-dashes (—) sparingly; one or two per page at most.
   - Semicolons sparingly.
   - Colons at most ~1 per 100 words in running prose.
   - A rhetorical question occasionally, only if it fits the voice.

---

## 3. Sentence Opener Variety

Robotic prose relies heavily on subject-first openers or monotonous demonstratives. 

### Forbidden Opener Chaining
- Never start two adjacent sentences with "The...", "This...", "It...", or "By...".

### Target Opener Rotation
Rotate sentence beginnings using diverse grammatical structures:
- **Prepositional phrases:** *"In early testing...", "Across four continents..."*
- **Adverbial clauses:** *"Inevitably, the code crashed...", "Quietly, the policy shifted..."*
- **Dependent / Participial clauses:** *"Having reviewed the telemetry...", "Faced with mounting pressure..."*
- **Coordinating conjunctions (Conversational & Natural):** *"And that changed everything.", "But the team pushed back."*
- **Infinitive phrases:** *"To survive the quarter, they cut prices."*
