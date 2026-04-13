# decisions.md
## Architecture Decision Records — PHANTOM-3B

> *"Max Tennyson makes decisions from experience. Every PHANTOM decision is documented here so future-you understands why."*

ADR format: **Context → Decision → Rationale → Consequences → Status**

---

## ADR-001: Parent Model Selection — Qwen2.5-3B + Phi-3.5-mini

**Date:** Week 2, Day 1
**Status:** Accepted

### Context

PHANTOM-3B is a cross-model merge. The choice of parent models is the single most important decision in the project — it determines whether the merge produces a genuinely better hybrid or just a noisier version of one parent.

Candidate pairs evaluated:

```
Option A: Qwen2.5-3B + Phi-3.5-mini
Option B: Llama-3.2-3B + Phi-3.5-mini
Option C: Qwen2.5-3B + Qwen2.5-3B-Instruct (same family)
Option D: Mistral-7B + Phi-3.5-mini (too large for RTX 2050)
```

### Decision

**Option A: Qwen2.5-3B-Instruct + Phi-3.5-mini-instruct**

### Rationale

1. **Complementary strengths (verified):** Qwen2.5-3B ranks high on MMLU reasoning benchmarks. Phi-3.5-mini ranks high on HumanEval (code). Neither model is dominant in both categories — this is the prerequisite for a good merge.

2. **3B scale fits RTX 2050:** Both models run in bfloat16 within 4GB VRAM. Inference and merging both possible on development hardware.

3. **Compatible architecture:** Both use transformer decoder architectures with similar layer counts. `--allow-crimes` handles the minor incompatibilities.

4. **Apache 2.0 license:** Both are Apache 2.0. The merged model can be published publicly without license conflicts.

5. **Differentiation from common merges:** The Llama/Mistral merge ecosystem is saturated. Qwen + Phi is unusual — more likely to stand out on HuggingFace.

### Consequences

- Positive: Strong complementary profile → high probability of benchmark improvement
- Positive: License-compatible → public HuggingFace publish
- Negative: Cross-family merge (different tokenizers, different embedding layers) → need `--allow-crimes` and `tokenizer_source: union`
- Risk: Tokenizer union may produce suboptimal handling of tokens unique to each parent

---

## ADR-002: Merge Method — Run Both SLERP and TIES, Compare

**Date:** Week 2, Day 1
**Status:** Accepted

### Context

MergeKit supports multiple merge methods. The project could run just one and publish it, or run multiple and compare.

### Decision

**Run SLERP and TIES+DARE independently. Benchmark both. Publish the winner.**

### Rationale

1. **Scientific credibility:** Running one merge config and claiming it "works" is weak. Running two and showing which is better demonstrates actual understanding of the tradeoffs.

2. **TIES+DARE expected to outperform:** Research evidence favors TIES+DARE for cross-domain merges. But SLERP is faster to produce and provides a baseline.

3. **Two merge configs = more content:** Two approaches, two model outputs, a comparison table — this is richer portfolio content than a single merge.

4. **Time budget allows it:** SLERP runs in ~8 minutes, TIES in ~9 minutes. Total: 17 minutes. Well within the 45-minute window allocated for merging.

### Consequences

- Positive: Comparison table shows depth of understanding
- Positive: If TIES underperforms (rare), SLERP is available as fallback
- Negative: Doubles storage requirement (two ~6.5GB model directories)
- Negative: Doubles benchmark time (two extra model evaluations)

---

## ADR-003: DARE Density — 0.7 (not 0.9 from original paper)

**Date:** Week 2, Day 1
**Status:** Accepted

### Context

The original DARE paper (Yu et al., 2024) uses `density=0.9` — dropping 90% of delta parameters. This was calibrated on 7B+ models.

### Decision

**Use `density=0.7` for PHANTOM-3B (3B scale).**

### Rationale

The DARE paper's density hyperparameter was calibrated on larger models where redundancy in fine-tuned delta parameters is higher. At 3B parameters, the delta space is smaller — dropping 90% removes too many non-redundant parameters, causing the merged model to lose coherence.

Community experiments on MergeKit (3B scale models) consistently report better performance at density 0.7–0.8 compared to 0.9.

**Evidence:**
- MergeKit community benchmark (HF forum, 2024): 3B merges at density=0.9 showed -1.2 average score vs density=0.7
- Theoretical basis: smaller models have proportionally fewer redundant parameters

### Consequences

- Positive: Better preservation of each parent's fine-tuned capability
- Positive: Less interference due to over-aggressive dropping
- Negative: Slightly more interference than density=0.9 (by design — acceptable)
- If performance is poor: increase density to 0.8 as first tuning step

---

## ADR-004: Tokenizer Strategy — Union

**Date:** Week 2, Day 1
**Status:** Accepted

### Context

Qwen2.5-3B and Phi-3.5-mini have different tokenizers with different vocabularies. The merged model needs a single tokenizer.

Options:
- `base`: Use the base model's tokenizer (Qwen's)
- `primary`: Same as base
- `union`: Merge both tokenizers, keeping all unique tokens from both

### Decision

**`tokenizer_source: union`**

### Rationale

- Using `base` would discard Phi's special tokens — any instructions or system prompt tokens specific to Phi's training format would be missing
- `union` adds ~2,000 tokens to the vocabulary but ensures both parents' instruction formats work
- The cost (slightly larger embedding table) is acceptable at 3B scale

### Consequences

- Positive: Both chat templates work correctly
- Positive: No special instruction tokens lost from either parent
- Negative: Merged model has a slightly larger vocabulary than either parent
- Risk: The ~2,000 added tokens have no corresponding trained embeddings — they are interpolated and may produce suboptimal outputs for extremely parent-specific prompts

---

## ADR-005: Inference Runtime — HuggingFace Transformers (Primary)

**Date:** Week 2, Day 1
**Status:** Accepted

### Context

For the Streamlit demo, the merged model needs to be called for inference. Options:

- HuggingFace Transformers (direct Python)
- Ollama (local REST server)
- HuggingFace Inference API (cloud)
- llama.cpp (GGUF format)

### Decision

**HuggingFace Transformers as primary. Ollama as documented alternative.**

### Rationale

1. **Simplicity:** Transformers is already installed for merging. No additional setup.
2. **Full control:** Direct access to generation parameters, logits, attention (useful for debugging)
3. **VRAM fits:** bfloat16 3B model fits in 4GB RTX 2050 VRAM
4. **No server to manage:** Transformers runs in-process with Streamlit — no separate server process

Ollama is documented in the runbook as an alternative for faster inference (it's more optimized for serving) and for sharing with others who don't want to set up the full Python environment.

### Consequences

- Positive: Simple setup, no additional infrastructure
- Positive: Works immediately after merge completes
- Negative: Slower than llama.cpp or Ollama for inference
- Negative: Model must fit in RAM/VRAM (no CPU offloading by default)

---

## ADR-006: Database — SQLite (not Redis, not Postgres)

**Date:** Week 2, Day 1
**Status:** Accepted

### Context

The Streamlit demo needs session persistence for chat history. Options: SQLite, Redis, Postgres, in-memory (dict).

### Decision

**SQLite via Python's built-in `sqlite3` module.**

### Rationale

1. **Zero additional dependencies:** sqlite3 is in Python's standard library
2. **Zero infrastructure:** No server to run, no connection strings
3. **Sufficient for scale:** A portfolio demo will never exceed SQLite's limits
4. **Portable:** The `database/phantom.db` file ships with the repo for reproducibility

In-memory (dict) was rejected because it loses all chat history on Streamlit rerun. Redis and Postgres are overkill for a single-user demo.

### Consequences

- Positive: Single-file database, easy to inspect with DB Browser for SQLite
- Positive: No setup required — `db.py` creates the file on first run
- Negative: Not suitable for multi-user deployment (lock contention)
- Negative: No real-time features (no pub/sub for live benchmarking)

---

*New ADRs are added when a significant technical decision is made that a future engineer (or future-you) would need to understand. Trivial implementation choices (variable names, helper function signatures) don't need ADRs.*
