# Playbook 02: Procedural Skills & Writing Rubrics

> **Part of the ADK Multi-Agent Text Humanizer Development Playbook**  
> **Location:** `skills/` directory

---

## 1. What are Procedural Skills in Google ADK?

Instead of bloating system instructions with thousands of words of static rules, Google ADK agents leverage **Procedural Skills**—modular, versioned Markdown documents stored under `skills/<skill-name>/SKILL.md`.

Agents dynamically read these rubrics or import them during initialization. This decouples linguistic domain knowledge from agent orchestration logic:

```text
skills/
├── human-cadence-standard/
│   └── SKILL.md                # Sentence length variance & rhythmic modulation
├── anti-ai-cliche-lexicon/
│   └── SKILL.md                # 150+ banned AI phrases & human replacements
├── tone-rubrics/
│   └── SKILL.md                # Conversational, Executive, Academic, and Narrative styles
└── academic-detector-rubrics/
    └── SKILL.md                # Turnitin, GPTZero, and CopyLeaks vulnerability mitigation
```

---

## 2. Skill 1: The Human Cadence Standard

Human writing has a recognizable rhythmic signature: high burstiness.
- **Short sentences (3–8 words):** Create emphasis, rhythm, and clarity.
- **Medium sentences (9–18 words):** Advance narrative or develop arguments.
- **Long complex sentences (19–35+ words):** Synthesize interrelated concepts.

### Quantitative Benchmark:
- AI prose typically exhibits a sentence length standard deviation ($\sigma$) of **3.0 to 5.0**.
- The `HumanizerOrchestrator` quality gate enforces a minimum standard deviation $\sigma \ge 8.0$ (or substantial improvement over baseline).

---

## 3. Skill 2: Anti-AI Cliché Lexicon

LLM alignment datasets over-index on corporate diplomacy and academic neutrality. The anti-cliché rubric bans over 150 dead giveaways:

| Category | Banned AI Words / Phrases | Organic Human Replacements |
| :--- | :--- | :--- |
| **Pompous Metaphors** | *"tapestry"*, *"beacon"*, *"mosaic"*, *"orchestration"* | Drop the metaphor; describe the reality directly |
| **Fake Depth** | *"testament to"*, *"delve into"*, *"shed light on"* | *"shows"*, *"proves"*, *"examine"*, *"uncover"* |
| **Formulaic Adverbs** | *"Moreover,"*, *"Furthermore,"*, *"In conclusion,"* | Organic transitions, semicolons, or start directly with the point |
| **Hype Adjectives** | *"pivotal"*, *"groundbreaking"*, *"transformative"* | Specific metrics, dates, and concrete details |

---

## 4. Skill 3: Persona & Tone Rubrics

The system adjusts rewriting styles across four primary personas:
1. **Conversational / Casual:** Natural contractions, rhetorical pacing, first-person anecdotes where context allows.
2. **Executive / Professional:** Direct, bottom-line-first (BLUF), active verbs, high signal-to-noise ratio.
3. **Academic / Scholarly:** Deep relational synthesis, discipline-specific terminology, active voice, integrated citations.
4. **Narrative / Storyteller:** Cinematic pacing, sensory grounding, varied paragraph structure.

---

## 5. Skill 4: Academic & AI Detector Vulnerability Rubrics

AI detectors (Turnitin, GPTZero, CopyLeaks) analyze specific statistical artifacts:
- **Template Openings:** Starting 3+ sentences consecutively with participle phrases (*"By analyzing..."*, *"Having considered..."*).
- **Unintegrated Citations:** Hanging citation brackets at sentence ends without lead-in signal phrases (*"according to Smith (2024)"*).
- **Isolated Stub Paragraphs:** Single-sentence orphan paragraphs typical of ChatGPT summaries.
- **Relational Synthesis:** AI lists points sequentially; humans synthesize how point A constrains or complicates point B.
