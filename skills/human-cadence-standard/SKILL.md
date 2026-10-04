# Human Cadence & Syntactic Rhythm Standard

This skill establishes the syntactic and rhythmic architecture for authentic human writing, combating the mechanical monotony typical of Large Language Models.

---

## 1. The Principle of Burstiness (Sentence Length Variance)

Large Language Models generate text with uniform sentence lengths (typically clustering tightly around 15–20 words with standard deviation < 5.0). Human writing breathes, accelerates, pauses, and surges.

### Target Distribution
- **Overall Standard Deviation:** Must exceed **8.0** words per sentence.
- **Micro-Sentences (3–8 words):** ~20% of text. Used for declarative punches, transitions, questions, and emphasis.
- **Medium Sentences (12–18 words):** ~50% of text. Used for linear narrative and connecting ideas.
- **Complex Sentences (22–35 words):** ~30% of text. Used for layered context, nuanced explanations, and rich illustration.

### Cadence Pattern Examples
> **Robotic Uniformity (Negative Pattern):**
> "The implementation of artificial intelligence in healthcare has revolutionized patient diagnostics. Medical professionals can now analyze radiological imagery with unprecedented speed. Furthermore, administrative workflows have been significantly streamlined across hospital systems. This transition represents a major milestone in modern clinical care." *(Sentence lengths: 10, 11, 10, 10 — Stdev: 0.5)*

> **Human Cadence (Positive Pattern):**
> "AI changed hospital diagnostics almost overnight. Radiologists who once spent hours squinting at inconclusive scans now get instant second opinions from neural networks trained on millions of clinical records. The paperwork shrank, too. It wasn't seamless, but the payoff arrived faster than anyone predicted." *(Sentence lengths: 6, 23, 4, 11 — Stdev: 7.6)*

---

## 2. Anti-Monotony Guardrails

1. **The Rule of Three:** Never allow three consecutive sentences to fall within 3 words of one another in length.
2. **Periodic Reset:** Every paragraph of 3 or more sentences must contain at least one sentence under 8 words.
3. **Intentional Fragments:** When appropriate for tone, single-clause declarations or deliberate fragments are permitted to break flow.
4. **Punctuation Diversity:**
   - Use em-dashes (—) to insert organic conversational pivots.
   - Use semicolons sparingly—only when connecting two tightly coupled thoughts.
   - Inject occasional rhetorical questions or direct appeals to engage the reader.

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
