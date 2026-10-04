# Playbook 03: Linguistic Tooling & FastMCP Server

> **Part of the ADK Multi-Agent Text Humanizer Development Playbook**  
> **Tooling:** FastMCP, Python Standard Library, Deterministic Algorithms  
> **Location:** `tools/` and `mcp_servers/linguistic_tools/`

---

## 1. Grounding LLMs with Deterministic Tooling

As established in the workshop's central principle:  
> **"Fluency is not evidence."**  
> A model without tools can generate smooth text that secretly retains low burstiness and high cliché density. To guarantee results, we ground the agents in deterministic Python algorithms.

---

## 2. The Core Tooling Suite (`tools/`)

### A. Linguistic Metrics Calculator (`tools/metrics.py`)
Computes telemetry consumed by `diagnostic_agent` and `critic_agent`:
- **Burstiness ($\sigma$):** Computes sentence length standard deviation across words.
- **Cliché Density:** Regular-expression matching against 150+ compiled AI buzzwords.
- **Opener Repetition:** Detects sequential duplicate grammatical openers.
- **Human-Likeness Index (HLI, 0–100%):** A composite score weighted by burstiness, cliché penalty, opener diversity, and paragraph rhythm.

```python
from tools.metrics import analyze_linguistic_metrics

metrics = analyze_linguistic_metrics(sample_text)
print(f"Burstiness Stdev: {metrics['burstiness']['stdev']}")
print(f"Clichés Found: {metrics['ai_cliches']['count']}")
print(f"Human-Likeness Index: {metrics['human_likeness_index']}%")
```

### B. Semantic & Factual Diff Calculator (`tools/diff.py`)
Used by `critic_agent` to enforce **100% factual fidelity**:
- Compares original and rewritten texts to ensure critical entities (names, numbers, dates, domain terms) are preserved.
- Produces before-and-after scorecard deltas.

---

## 3. Packaging Tools via FastMCP (`mcp_servers/linguistic_tools/server.py`)

The Model Context Protocol (MCP) enables tools to be exposed as modular RPC endpoints across agents and external clients:

```python
"""FastMCP Linguistic Tools Server."""

from fastmcp import FastMCP
from tools.metrics import analyze_linguistic_metrics
from tools.diff import compare_texts

# Initialize FastMCP Server
mcp = FastMCP("linguistic-tools-server")

# Expose linguistic telemetry tool
@mcp.tool()
def get_linguistic_metrics(text: str) -> dict:
    """Analyze sentence burstiness, AI clichés, and compute Human-Likeness Index."""
    return analyze_linguistic_metrics(text)

# Expose comparative auditing tool
@mcp.tool()
def get_text_comparison(original_text: str, rewritten_text: str) -> dict:
    """Compare two texts to compute metric deltas and verify factual fidelity."""
    return compare_texts(original_text, rewritten_text)

if __name__ == "__main__":
    mcp.run()
```

---

## 4. Running and Inspecting MCP Servers

You can test the FastMCP linguistic server directly via the FastMCP CLI or Python:

```bash
# Run FastMCP in development / inspector mode
fastmcp dev mcp_servers/linguistic_tools/server.py
```
This launches the interactive MCP browser UI where you can invoke `get_linguistic_metrics` and inspect parameter schemas and JSON responses in real time.
