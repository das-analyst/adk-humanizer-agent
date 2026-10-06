# Academic & AI-Detector Anti-Pattern Rubric (Turnitin / Detector Mitigation Standard)

This skill operationalizes a 10-point linguistic and rhetorical rubric designed to eliminate machine-learning hallmarks frequently flagged by AI detectors (such as Turnitin, GPTZero, and CopyLeaks). It transforms robotic, synthetic prose into authentic, analytical, and voice-driven writing.

---

## 1. The 10 AI Detector Anti-Patterns & Human Alternatives

### 1️⃣ Repetition & Predictable Rhythm
- **AI-Like Pattern:** Sentences with identical parallel structures or rhythmic pacing (especially tripartite lists of verbs or adjectives).
  - *Example:* *"It presents their features, emphasizes their strengths, and explains their benefits."*
- **Human Revision Standard:** Asymmetrical phrasing, varying grammatical roles, and dynamic sentence shapes.
  - *Example:* *"This comparison highlights key features of each method and explains how their strengths complement one another."*

### 2️⃣ Generic or Overly Polished Language
- **AI-Like Pattern:** Grammatically flawless but vague, interchangeable adjectives (*significant, important, effective, essential, crucial, vital, prominent, comprehensive*).
  - *Example:* *"Effective tools for analysis."*
- **Human Revision Standard:** Replace broad adjectives with field-specific nouns and concrete operational verbs.
  - *Example:* *"Scalable tools for database performance analysis."*

### 3️⃣ Lack of Depth or Synthesis
- **AI-Like Pattern:** Serial summarization where paragraphs list facts without linking them together or explaining the relationship between concepts.
  - *Example:* *"Use Case Diagrams and DFDs show different perspectives. Use Case Diagrams focus on users. DFDs focus on data."*
- **Human Revision Standard:** Link related facts with a plain connector, once where it helps. Do **not** apply a "While X…, Y…—together…" frame throughout: used repeatedly it becomes its own AI signature (see item 12). Cutting one of two redundant points is often better than fusing them.
  - *Example:* *"Use Case Diagrams map who does what; DFDs trace where the data goes."*

### 4️⃣ Impersonal, Template-Based Openings
- **AI-Like Pattern:** Throat-clearing meta-announcements (*"This paper will discuss..."*, *"The purpose of this study is to examine..."*, *"In conclusion, this essay explains..."*).
  - *Example:* *"This paper will discuss modern cloud architectures and their security challenges."*
- **Human Revision Standard:** Immediate, substantive analytical entry with purposeful framing.
  - *Example:* *"By contrasting distributed microservices with monolithic deployments, this analysis isolates the primary security vectors in modern cloud infrastructure."*

### 5️⃣ Overuse of Transitions & Stock Phrases
- **AI-Like Pattern:** Monotonous paragraph-initial or sentence-initial connectors (*Moreover, Furthermore, Additionally, In conclusion, Consequently*).
  - *Example:* *"Furthermore, memory usage increases. In addition, latency degrades."*
- **Human Revision Standard:** Organic cohesion through idea progression, varied sentence-internal connectors (*"Another key factor is..."*, *"A related challenge involves..."*, *"Beyond the immediate cost..."*), or direct juxtaposition.

### 6️⃣ Perfect Uniformity with No Voice
- **AI-Like Pattern:** Flat, bloodless, detached third-person neutrality with zero authorial perspective or reasoning reflection.
- **Human Revision Standard (Context-Aware First Person):**
  - When an author, team, or project context is present or implied: Use natural first-person (*"In this project, I analyzed..."*, *"We discovered that..."*).
  - For objective documentation: Inject reflective analytical reasoning (*"This suggests that..."*, *"A likely explanation is..."*, *"A closer look reveals..."*) without fabricating personal claims.

### 7️⃣ Dropped Citations or No Signal Phrases
- **AI-Like Pattern:** Parenthetical citations dumped at the end of a sentence without rhetorical attribution or context.
  - *Example:* *"Microservices improve deployment velocity (Smith, 2023)."*
- **Human Revision Standard (Signal Phrase Integration):**
  - Integrate citations into the argument with contextual signal phrases (*"According to Smith (2023)..."*, *"As recent empirical trials confirm (Johnson et al., 2022)..."*, *"Chen and Lee (2024) observed that..."*).
  - *Note:* In non-academic or general prose, bare parentheticals receive advisory improvement suggestions rather than hard gate rejections.

### 8️⃣ Short, Isolated Paragraphs
- **AI-Like Pattern:** Choppy, bullet-like "island" paragraphs (1–2 sentences each) that summarize a single isolated thought without transitional bridges.
- **Human Revision Standard:** Multi-layered paragraph progression (topic claim $\rightarrow$ evidence/synthesis $\rightarrow$ consequence/bridge).
  - *Graceful Degradation:* This check is waived for inputs under 100 words, executive bullet summaries, or single-sentence prompts.

### 9️⃣ Mechanical Introductions & Conclusions
- **AI-Like Pattern:** Formulaic mirror summaries that mechanically restate the introduction (*"In conclusion, we have seen that X, Y, and Z are important..."*), **and** grand quotable closers (*"…achieve together what no individual could ever achieve alone."*).
- **Human Revision Standard:** A short, plain ending (2–4 sentences): what the author learned or will do. No mic-drop line, no mirrored restatement.

### 🔟 Artificial Perfection
- **AI-Like Pattern:** Unnaturally clean, symmetrical prose where every section has the same shape and every paragraph resolves neatly.
- **Human Revision Standard:** Uneven section lengths, some paragraphs without a tidy lesson, plain spoken-register wording, hedges (*"I tend to"*, *"I need to"*), occasional informal phrasing. Burstiness is advisory only; it did not distinguish a passing human paper from a flagged AI draft.

### 1️⃣1️⃣ "Not X but Y" Contrast Pivots
- **AI-Like Pattern:** *"X is not Y: it is Z"*, *"not merely X but Y"*, *"not about X; it is about Y"*.
- **Human Revision Standard:** State the positive claim directly. At most one such construction per document.

### 1️⃣2️⃣ Repeated Paragraph Shape
- **AI-Like Pattern:** Each section follows *strength → anecdote → "However, my self-assessment reveals…" → lesson*; consecutive paragraphs open with contrast pivots.
- **Human Revision Standard:** Vary the shape per section; at most one pivot-opening paragraph per 800 words.

### 1️⃣3️⃣ Colon and Tricolon Density
- **AI-Like Pattern:** Many colons in running prose (more than ~1 per 100 words) and constant three-item series (*"shared power, cultivating autonomy, and building self-efficacy"*).
- **Human Revision Standard:** Commas and plain sentences; vary list lengths (2, 4, or a sentence).

### 1️⃣4️⃣ No Concrete Detail
- **AI-Like Pattern:** Polished abstract claims with no named project, number, incident, or personal moment.
- **Human Revision Standard:** Anchor each major section in a specific from the source text or the user's `VOICE_PROFILE:`. **Never invent one.** If none exists, say so under *Authenticity Slots* rather than fabricating.

> See `human-voice-patterns/SKILL.md` for the full pattern list, plain-word replacements, and casual-slips rules.

---

## 2. The Synthesis Matrix

When transforming consecutive summaries into analytical synthesis:

| Summary Mode (Robotic) | Synthesis Formula | Humanized Output Example |
| :--- | :--- | :--- |
| Concept A does X. Concept B does Y. | **Contrastive Subordination:**<br>*"While [Concept A] [does X], [Concept B] [does Y]—[shared outcome]."* | *"While manual testing catches surface regressions, automated unit suites safeguard core business logic—together establishing a resilient release pipeline."* |
| Tool 1 is good. Tool 2 is also useful. | **Qualitative Nuance:**<br>*"[Tool 1] excels at [strength], but [Tool 2] proves indispensable when [condition]."* | *"Redis handles lightning-fast cache retrieval, but PostgreSQL proves indispensable when transactional integrity cannot be compromised."* |
| Event occurred. Then result happened. | **Causal Integration:**<br>*"[Root cause] forced [pivot], ultimately yielding [insight]."* | *"Mounting database lock contention forced the team to rethink synchronous writes, ultimately leading to an event-driven queue."* |

---

## 3. Signal Phrase Catalog for Citation Integration

Rotate signal phrases across categories to prevent formulaic attribution:

- **Empirical Confirmation:** *"According to [Author] ([Year])..."*, *"As [Author] demonstrated..."*, *"Recent findings by [Author] confirm that..."*
- **Analytical Argumentation:** *"[Author] argues that..."*, *"In their evaluation, [Author] suggested that..."*, *"[Author] established a link between..."*
- **Contrastive Perspective:** *"In contrast to earlier claims, [Author] revealed..."*, *"[Author] challenged this assumption by showing..."*
