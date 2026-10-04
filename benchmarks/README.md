# Empirical Humanization Benchmarks & Test Cases

This directory contains paired before-and-after benchmarks evaluating the multi-agent system across different writing domains and personas. Each case study documents the raw AI input, the humanized prose, and the empirical telemetry score deltas.

---

## Benchmark Summary

| Case Study | Domain | Target Persona | Baseline HLI | Final HLI | Burstiness Delta ($\Delta \sigma$) | AI Detector Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| [**Case 01**](01-corporate-strategy-memo.md) | Corporate Strategy | Executive / BLUF | `38.2%` | `92.4%` | **+6.8** (3.1 $\rightarrow$ 9.9) | Clean / Human Passed |
| [**Case 02**](02-academic-literature-review.md) | Academic Paper | Scholarly / Rigorous | `44.0%` | `90.8%` | **+7.1** (4.2 $\rightarrow$ 11.3) | Turnitin Risk Reduced |
| [**Case 03**](03-technical-engineering-blog.md) | Tech Blog | Conversational / Punchy | `35.7%` | `94.1%` | **+8.4** (2.9 $\rightarrow$ 11.3) | Clean / Human Passed |

---

## Benchmark Evaluation Dimensions

1. **Burstiness ($\sigma$):** Standard deviation of sentence lengths (word count). Monotonous AI prose scores $< 4.5$; natural human writing scores $\ge 8.0$.
2. **AI Cliché & Buzzword Count:** Occurrences of overused alignment phrases (*"delve into"*, *"testament to"*, *"tapestry"*, *"game changer"*, etc.). Target: **0**.
3. **Opener Variance Ratio:** Proportion of distinct grammatical sentence openings. Target: **$\ge 0.85$**.
4. **Factual Fidelity:** 100% preservation of verified entities, metrics, dates, and technical logic.
