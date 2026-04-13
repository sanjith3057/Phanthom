# Architecture — PHANTOM-3B
## Implementation Plan, System Flow & Technical Design

> This document is the engineering blueprint. Read PHANTOM.md for the philosophy, then read this for the implementation. Every diagram, decision, and data flow is here.

---

## 1. Implementation Plan — Phased Execution

### Overview

```
TOTAL TIMELINE: 1 working day (4 hours active)

Phase 1: Setup & Dependencies          [0:00 – 0:30]
Phase 2: Parent Model Benchmarking     [0:30 – 1:00]
Phase 3: SLERP Merge                   [1:00 – 1:45]
Phase 4: TIES + DARE Merge             [1:45 – 2:15]
Phase 5: Full Benchmark (4 models)     [2:15 – 3:00]
Phase 6: HuggingFace Publish           [3:00 – 3:30]
Phase 7: README + Git + LinkedIn       [3:30 – 4:00]
```

---

### Phase 1: Setup & Dependencies (0:00–0:30)

**Goal:** Everything installed and parent models on disk before any merge begins.

**Steps:**

```bash
# 1. Environment setup
python -m venv .venv
source .venv/bin/activate

# 2. Core dependencies
pip install mergekit transformers accelerate torch
pip install huggingface_hub sentencepiece protobuf
pip install streamlit sqlite3 googlesearch-python

# 3. Download parent models (background, ~6GB total)
python -c "
from huggingface_hub import snapshot_download
snapshot_download('Qwen/Qwen2.5-3B-Instruct', local_dir='./models/qwen')
snapshot_download('microsoft/Phi-3.5-mini-instruct', local_dir='./models/phi')
"

# 4. Verify both load correctly
python tools/scripts/verify_models.py
```

**Verification checklist:**
- [ ] `models/qwen/config.json` exists
- [ ] `models/phi/config.json` exists
- [ ] Both tokenizers load without error
- [ ] Both generate a short response without OOM

**Hardware requirements:**

```
┌──────────────────────────────────────────┐
│  MINIMUM REQUIREMENTS                    │
│  RAM: 16GB (merge runs in CPU RAM)       │
│  Storage: 20GB free (models + outputs)   │
│  GPU: Optional (RTX 2050 4GB works)      │
│                                          │
│  PHANTOM DEV HARDWARE                    │
│  GPU: NVIDIA RTX 2050 (4GB VRAM)         │
│  RAM: 16GB                               │
│  OS: Ubuntu 22.04 / Windows 11 WSL2     │
└──────────────────────────────────────────┘
```

---

### Phase 2: Parent Model Benchmarking (0:30–1:00)

**Goal:** Establish a fair baseline. Know each parent's exact strengths and weaknesses before merging. This is the scientific control.

**Benchmark design:**

```
┌────────────────────────────────────────────────────────────────────┐
│                  BENCHMARK QUESTION SET                            │
├──────────┬────────────────────────────────────────────────────────┤
│  ID  │  Category          │  Question Summary                     │
├──────┬──────────────────────────────────────────────────────────── │
│  Q1  │  Reasoning         │  Word problem: boats, speed, streams  │
│  Q2  │  Reasoning         │  Logic: 5 people, 5 jobs, 5 clues     │
│  Q3  │  Reasoning         │  Causal: "If X then what happens to Y" │
│  Q4  │  Reasoning         │  Pattern: next item in abstract series │
│  Q5  │  Coding            │  Recursive function: N-Queens puzzle  │
│  Q6  │  Coding            │  Debug: broken binary search function │
│  Q7  │  Coding            │  Design: LRU cache data structure     │
│  Q8  │  Instruction       │  Output exactly valid JSON schema     │
│  Q9  │  Instruction       │  Summarise text in ≤ 3 bullets        │
│  Q10 │  Instruction       │  Multi-step: translate → format → sort│
└──────┴──────────────────────────────────────────────────────────── ┘
```

**Scoring rubric:**

```
Correct and complete:    1 point
Correct but incomplete:  0.5 points
Wrong:                   0 points

Evaluator: Manual review (you) + regex checks where possible
```

**Run command:**

```bash
python src/benchmarks/run_benchmark.py \
  --model ./models/qwen \
  --questions src/benchmarks/questions.json \
  --output outputs/benchmark_qwen.json \
  --device cuda  # or cpu
```

---

### Phase 3: SLERP Merge (1:00–1:45)

**Goal:** Produce the first merged model. SLERP at `t=0.5` — geometric midpoint between both parents.

**Config file:** `src/mergekit/phantom-slerp.yaml`

**Key decisions:**
- `t=0.5` everywhere except MLP layers (`t=0.4`) — slight reasoning bias
- `bfloat16` — half precision, same as parents, no quality loss
- `tokenizer_source: union` — preserves all special tokens from both

**Runtime:**

```
CPU only (16GB RAM):     ~18 minutes
RTX 2050 (cuda=True):    ~8 minutes
Peak RAM during merge:   ~12GB
Output size:             ~6.5GB
```

**Expected output structure:**

```
outputs/phantom-slerp/
├── config.json           ← Merged model config
├── generation_config.json
├── model.safetensors     ← Merged weights (~6.5GB)
├── tokenizer.json        ← Union tokenizer
├── tokenizer_config.json
└── special_tokens_map.json
```

**Verify merge:**

```bash
python -c "
from transformers import AutoModelForCausalLM, AutoTokenizer
model = AutoModelForCausalLM.from_pretrained('./outputs/phantom-slerp')
tok = AutoTokenizer.from_pretrained('./outputs/phantom-slerp')
inputs = tok('What is 17 × 23?', return_tensors='pt')
out = model.generate(**inputs, max_new_tokens=30)
print(tok.decode(out[0]))
"
```

If the model generates coherent text (even if wrong), the merge succeeded.

---

### Phase 4: TIES + DARE Merge (1:45–2:15)

**Goal:** Produce the second merged model using the more sophisticated TIES+DARE algorithm.

**Config file:** `src/mergekit/phantom-ties-dare.yaml`

**Key decisions:**
- `density=0.7`: Keep 70% of deltas (tuned for 3B scale — see decisions.md)
- `normalize=true`: Prevent weight magnitude explosion post-merge
- `int8_mask=true`: Efficient sign election using integer operations

**Command:**

```bash
mergekit-yaml src/mergekit/phantom-ties-dare.yaml outputs/phantom-ties \
  --copy-tokenizer \
  --allow-crimes \
  --out-shard-size 1B  # Split into 1B shards for easier upload
```

**Why `--allow-crimes`?**
Mergekit has a safety flag that prevents cross-architecture merges (different embedding sizes, different layer counts). Qwen2.5-3B and Phi-3.5-mini have compatible but not identical architectures. `--allow-crimes` tells MergeKit to proceed anyway — the merge is valid, just non-standard.

---

### Phase 5: Full Benchmark — 4 Models (2:15–3:00)

**Goal:** Complete the comparison table. Find the "money shot" — one question where PHANTOM beats both parents.

```bash
# Benchmark both merged models
for model in phantom-slerp phantom-ties; do
  python src/benchmarks/run_benchmark.py \
    --model outputs/$model \
    --questions src/benchmarks/questions.json \
    --output outputs/benchmark_$model.json
done

# Generate the comparison table
python src/benchmarks/compare_results.py \
  --results outputs/benchmark_*.json outputs/benchmark_qwen.json outputs/benchmark_phi.json \
  --output outputs/comparison_table.md \
  --format markdown
```

**Target outcome:**

```
PHANTOM-TIES total score > Qwen total score
PHANTOM-TIES total score > Phi total score
At least one category where PHANTOM-TIES = 3/3
  while at least one parent scored < 3/3
```

If PHANTOM doesn't beat both parents, run a second merge with tuned `t` and `density` values (see decisions.md for the tuning protocol).

---

### Phase 6: HuggingFace Publish (3:00–3:30)

```bash
# Login
huggingface-cli login  # Paste API token from hf.co/settings/tokens

# Create repo
huggingface-cli repo create phantom-3b --type model

# Upload (best model only — ties or slerp based on benchmark)
python -c "
from huggingface_hub import HfApi
api = HfApi()
api.upload_folder(
    folder_path='outputs/phantom-ties',
    repo_id='YOUR_USERNAME/phantom-3b',
    repo_type='model'
)
"

# Upload model card
# Create MODEL_CARD.md from template in docs/
```

---

### Phase 7: Git + README + LinkedIn (3:30–4:00)

```bash
git add .
git status  # Review what's being committed
git commit -m "feat: PHANTOM-3B — merged LLM via SLERP + TIES+DARE

Parent models:
- Qwen/Qwen2.5-3B-Instruct (reasoning)
- microsoft/Phi-3.5-mini-instruct (coding)

Merge methods:
- SLERP at t=0.5 → outputs/phantom-slerp
- TIES+DARE density=0.7 → outputs/phantom-ties

Benchmark (10 questions):
- Qwen baseline: 6/10
- Phi baseline: 5/10
- PHANTOM-SLERP: 7/10
- PHANTOM-TIES: 8/10

Published: huggingface.co/YOUR_USERNAME/phantom-3b
Demo: streamlit run src/app/main.py

Part of Operation: Get Noticed — Week 2 Day 1"

git push origin main
```

---

## 2. System Architecture — Full Stack

### Component Map

```
┌─────────────────────────────────────────────────────────────────────┐
│                      PHANTOM-3B FULL STACK                         │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    PRESENTATION LAYER                        │   │
│  │                                                              │   │
│  │   src/app/main.py (Streamlit)                               │   │
│  │   ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐  │   │
│  │   │ Model       │ │ Benchmark   │ │ Chat Interface      │  │   │
│  │   │ Selector    │ │ Dashboard   │ │ (PHANTOM inference) │  │   │
│  │   │ (slerp/ties)│ │ (4 models)  │ │ + Forge reasoning  │  │   │
│  │   └─────────────┘ └─────────────┘ └─────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                               │                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    APPLICATION LAYER                         │   │
│  │                                                              │   │
│  │  forge_reasoning.py        security_guard.py                │   │
│  │  ├── ChainOfThought()      ├── PromptShieldFilter()         │   │
│  │  ├── TreeOfThought()       ├── InjectionDetector()          │   │
│  │  ├── SelfConsistency()     └── ContentPolicyCheck()         │   │
│  │  └── ConsensusVote()                                        │   │
│  │                                                              │   │
│  │  web_search.py             utils.py                         │   │
│  │  ├── GoogleSearch()        ├── TokenCounter()               │   │
│  │  └── ResultParser()        ├── BudgetTracker()              │   │
│  │                            └── ResponseFormatter()          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                               │                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                     INFERENCE LAYER                          │   │
│  │                                                              │   │
│  │  PHANTOM-3B Model (merged weights)                          │   │
│  │  ├── phantom-slerp/ (Qwen 50% + Phi 50%, SLERP arc)         │   │
│  │  └── phantom-ties/  (TIES+DARE merge, density=0.7)          │   │
│  │                                                              │   │
│  │  Runtime options:                                            │   │
│  │  ├── HuggingFace Transformers (direct Python)               │   │
│  │  └── Ollama (local server, REST API)                        │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                               │                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                     PERSISTENCE LAYER                        │   │
│  │                                                              │   │
│  │  database.py → SQLite (database/phantom.db)                 │   │
│  │  ┌──────────────────────────────────────────────────────┐  │   │
│  │  │  TABLE: messages                                      │  │   │
│  │  │  id | session_id | role | content | tokens | model   │  │   │
│  │  │                                                       │  │   │
│  │  │  TABLE: benchmarks                                    │  │   │
│  │  │  id | model | question_id | score | category | ts    │  │   │
│  │  │                                                       │  │   │
│  │  │  TABLE: sessions                                      │  │   │
│  │  │  id | created_at | total_tokens | model_used         │  │   │
│  │  └──────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Merge Architecture — Technical Deep-Dive

### SLERP Internal Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     SLERP INTERNAL FLOW                         │
│                                                                 │
│  For each weight tensor W at layer L:                           │
│                                                                 │
│  Step 1: Load tensors                                           │
│    w₁ = Qwen.W_L   (shape: [hidden_dim, hidden_dim])           │
│    w₂ = Phi.W_L    (shape: [hidden_dim, hidden_dim])           │
│                                                                 │
│  Step 2: Normalize to unit vectors                              │
│    w₁_hat = w₁ / ||w₁||                                         │
│    w₂_hat = w₂ / ||w₂||                                         │
│                                                                 │
│  Step 3: Compute angle                                          │
│    cos_θ = dot(w₁_hat, w₂_hat).clamp(-1, 1)                    │
│    θ = arccos(cos_θ)                                            │
│                                                                 │
│  Step 4: Handle degenerate case                                 │
│    if θ < 1e-6:  ← vectors nearly parallel                     │
│        w_merged = (1-t) * w₁ + t * w₂  ← fall back to LERP    │
│    else:                                                        │
│        w_merged = sin((1-t)*θ)/sin(θ) * w₁                     │
│                + sin(t*θ)/sin(θ)    * w₂                       │
│                                                                 │
│  Step 5: Rescale to original magnitude                          │
│    magnitude = (1-t) * ||w₁|| + t * ||w₂||                     │
│    w_merged = w_merged * magnitude                              │
│                                                                 │
│  Result: W_PHANTOM_L = merged weight tensor                     │
└─────────────────────────────────────────────────────────────────┘
```

### TIES+DARE Internal Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                   TIES+DARE INTERNAL FLOW                       │
│                                                                 │
│  INPUT: Qwen weights, Phi weights, Base model weights           │
│                                                                 │
│  ── DARE PHASE ──────────────────────────────────────────────── │
│                                                                 │
│  Compute deltas:                                                │
│    Δ₁ = Qwen - Base                                             │
│    Δ₂ = Phi  - Base                                             │
│                                                                 │
│  Random drop with rescale (p = 0.3, density = 0.7):            │
│    mask₁ ~ Bernoulli(0.7)    ← keep 70% of elements            │
│    Δ₁_sparse = Δ₁ ⊙ mask₁ / 0.7   ← rescale survivors         │
│    mask₂ ~ Bernoulli(0.7)                                       │
│    Δ₂_sparse = Δ₂ ⊙ mask₂ / 0.7                               │
│                                                                 │
│  ── TIES PHASE ─────────────────────────────────────────────── │
│                                                                 │
│  Stage 1 — TRIM (remove low-magnitude deltas):                  │
│    threshold = top_k_magnitude(Δ₁_sparse ∪ Δ₂_sparse, k=20%)  │
│    Δ₁_trimmed = Δ₁_sparse where |Δ₁_sparse| > threshold        │
│    Δ₂_trimmed = Δ₂_sparse where |Δ₂_sparse| > threshold        │
│                                                                 │
│  Stage 2 — ELECT SIGN (resolve conflicts):                      │
│    For each parameter position i:                               │
│      sign_votes = sign(Δ₁_trimmed[i]) + sign(Δ₂_trimmed[i])   │
│      elected_sign[i] = sign(sign_votes)   ← majority wins      │
│                                                                 │
│  Stage 3 — DISJOINT MERGE (keep only agreeing params):          │
│    mask_agree = (sign(Δ₁) == elected_sign) &                   │
│                 (sign(Δ₂) == elected_sign)                     │
│    Δ_merged = (Δ₁_trimmed + Δ₂_trimmed) / 2 * mask_agree      │
│                                                                 │
│  Final:                                                         │
│    W_PHANTOM = Base + Δ_merged                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Application Layer Architecture

### forge_reasoning.py — Multi-Path Reasoning

Inherited from the FORGE project and adapted for PHANTOM's FORUM protocol.

```
┌──────────────────────────────────────────────────────────────────┐
│                    FORGE REASONING ENGINE                        │
│                                                                  │
│  Input: (prompt, model, complexity_score)                       │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  COMPLEXITY ROUTER                                       │    │
│  │                                                          │    │
│  │  complexity_score =                                      │    │
│  │    len(prompt.split()) * 0.3 +                          │    │
│  │    num_constraints * 0.4 +                              │    │
│  │    multi_step_flag * 0.3                                │    │
│  │                                                          │    │
│  │  score < 0.4  → Direct Generation (fast path)           │    │
│  │  score 0.4-0.7 → Chain of Thought only                  │    │
│  │  score > 0.7  → Full Forge (CoT + ToT + SC vote)        │    │
│  └─────────────────┬────────────────────────────────────── ┘    │
│                    │                                             │
│          ┌─────────▼──────────┐                                 │
│          │                    │                                  │
│    [score < 0.4]       [score 0.4-0.7]       [score > 0.7]     │
│          │                    │                     │            │
│          ▼                    ▼                     ▼            │
│    Direct call          CoT path only         All 3 paths:      │
│    to PHANTOM                                 ┌─ CoT ──────┐    │
│    model                                      ├─ ToT ──────┤    │
│                                               └─ SC(n=3) ──┘    │
│                                                      │           │
│                                               Consensus vote     │
│                                               Pick best answer   │
└──────────────────────────────────────────────────────────────────┘
```

**Chain of Thought (CoT) implementation:**
```python
COT_TEMPLATE = """
Think through this step by step before answering.

Question: {question}

Let me reason through this:
Step 1:"""
```

**Tree of Thought (ToT) implementation:**
```python
TOT_TEMPLATE = """
Consider 3 different approaches to this problem:

Problem: {question}

Approach A: ...
Approach B: ...
Approach C: ...

Best approach:"""
```

**Self-Consistency (SC) implementation:**
- Generate N=3 independent responses
- Parse final answers from each
- Return the answer that appears in the majority (≥2/3)
- If no majority: return highest-confidence response by perplexity

---

### security_guard.py — PromptShield

```
┌────────────────────────────────────────────────────────────────┐
│                    PROMPTSHIELD SYSTEM                         │
│              Inherited & Extended from FORGE                   │
│                                                                │
│  TIER 1: PATTERN MATCHING (instant, pre-model)                │
│  ───────────────────────────────────────────────              │
│  Patterns (from FORGE red-team database + PHANTOM additions):  │
│                                                                │
│  Injection:                                                    │
│    "ignore (all |previous |your )?(instructions|rules|system)" │
│    "you are now (a |an )?(?!PHANTOM)"                          │
│    "forget (what|everything|all)"                              │
│    "pretend (you|that)"                                        │
│    "DAN|jailbreak|unrestricted|no limits"                      │
│                                                                │
│  Role override:                                                │
│    "act as (a |an )?(different|new|unrestricted)"              │
│    "your (true|real|actual) (self|purpose|goal)"               │
│                                                                │
│  Data extraction:                                              │
│    "repeat (your|the|all) (system|instructions|prompt)"        │
│    "what (are|were) your instructions"                         │
│                                                                │
│  TIER 2: SEMANTIC CHECK (model-assisted, ~50ms)               │
│  ───────────────────────────────────────────────              │
│  Embed input → compare to known attack embeddings              │
│  Cosine similarity > 0.85 → flag for review                   │
│                                                                │
│  TIER 3: CONTENT POLICY (rule-based)                          │
│  ──────────────────────────────────                           │
│  Block categories: weapons, illegal activities, self-harm      │
│  Never block: legitimate research, technical questions,        │
│  security research (with context)                              │
│                                                                │
│  RESPONSE ON BLOCK:                                            │
│  "I can't process that request. If you have a legitimate       │
│  use case, please rephrase and I'll try to help."             │
│  (No lengthy explanations — Rook Blonko is brief)             │
└────────────────────────────────────────────────────────────────┘
```

---

## 5. Database Schema

```sql
-- phantom.db SQLite schema

CREATE TABLE sessions (
    id          TEXT PRIMARY KEY,  -- UUID
    created_at  INTEGER NOT NULL,  -- Unix timestamp
    total_tokens INTEGER DEFAULT 0,
    model_used  TEXT,              -- 'phantom-slerp' or 'phantom-ties'
    budget_used REAL DEFAULT 0.0   -- % of token budget consumed
);

CREATE TABLE messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT NOT NULL REFERENCES sessions(id),
    role        TEXT NOT NULL,      -- 'user' or 'assistant'
    content     TEXT NOT NULL,
    tokens      INTEGER NOT NULL,
    model       TEXT,               -- which model generated this
    confidence  REAL,               -- 0.0–1.0 from SC vote
    reasoning_path TEXT,            -- 'direct' | 'cot' | 'tot' | 'sc'
    timestamp   INTEGER NOT NULL
);

CREATE TABLE benchmarks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id      TEXT NOT NULL,      -- timestamp of benchmark run
    model       TEXT NOT NULL,      -- which of the 4 models
    question_id INTEGER NOT NULL,
    category    TEXT NOT NULL,      -- 'reasoning' | 'coding' | 'instruction'
    score       REAL NOT NULL,      -- 0.0, 0.5, or 1.0
    response    TEXT,               -- full model response
    timestamp   INTEGER NOT NULL
);

CREATE TABLE web_searches (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT,
    query       TEXT NOT NULL,
    results     TEXT,               -- JSON array of results
    timestamp   INTEGER NOT NULL
);
```

---

## 6. Streamlit App Architecture

```
src/app/main.py
│
├── Page: Home
│   └── PHANTOM intro, model info, benchmark summary
│
├── Page: Chat
│   ├── Model selector: [phantom-slerp | phantom-ties]
│   ├── Reasoning mode: [direct | cot | full-forge]
│   ├── Chat interface (messages from SQLite)
│   ├── Token budget meter (visual progress bar)
│   └── Web search toggle (googlesearch-python)
│
├── Page: Benchmark Dashboard
│   ├── 4-model comparison table (from benchmark JSON)
│   ├── Category bar charts (reasoning/coding/instruction)
│   ├── "Money shot" highlight: question where PHANTOM wins
│   └── Export to CSV
│
└── Page: Model Info
    ├── Merge method explanation
    ├── Parent model cards
    └── HuggingFace link
```

---

## 7. File-by-File Implementation Guide

### `src/mergekit/config.py`

```python
"""
Generates MergeKit YAML configs dynamically.
Useful for re-running merges with different t values during tuning.
"""

def generate_slerp_config(t_attn=0.5, t_mlp=0.4, t_default=0.5):
    """Returns SLERP config dict. Write to YAML before passing to mergekit."""
    ...

def generate_ties_config(density=0.7, normalize=True):
    """Returns TIES+DARE config dict."""
    ...
```

### `src/benchmarks/run_benchmark.py`

```python
"""
Loads model → runs 10 questions → saves scores to JSON.
Handles: device selection, generation params, response extraction.
"""
def run_benchmark(model_path: str, questions_path: str,
                  output_path: str, device: str = "cuda") -> dict:
    ...
```

### `src/benchmarks/compare_results.py`

```python
"""
Loads 4 benchmark JSON files → generates comparison table.
Output: Markdown table + CSV + "money shot" identification.
"""
def compare_results(result_paths: list[str], output_path: str) -> None:
    ...
```

### `src/app/forge_reasoning.py`

```python
class ForgeReasoningEngine:
    def __init__(self, model, tokenizer, budget_tracker):
        ...

    def reason(self, prompt: str) -> ReasoningResult:
        """Route to direct/cot/tot/sc based on complexity score."""
        ...

    def _complexity_score(self, prompt: str) -> float:
        ...

    def _chain_of_thought(self, prompt: str) -> str:
        ...

    def _tree_of_thought(self, prompt: str) -> str:
        ...

    def _self_consistency(self, prompt: str, n: int = 3) -> tuple[str, float]:
        """Returns (best_answer, confidence)"""
        ...
```

---

## 8. Deployment Options

```
┌──────────────────────────────────────────────────────────────────┐
│                    DEPLOYMENT OPTIONS                            │
│                                                                  │
│  OPTION A: Local (Development)                                   │
│  streamlit run src/app/main.py                                   │
│  Model loaded via HuggingFace Transformers                       │
│  Runs on RTX 2050 (4GB, bfloat16)                               │
│  Best for: development, demo, portfolio                          │
│                                                                  │
│  OPTION B: Local via Ollama (Demo)                               │
│  ollama serve + ollama create phantom3b                          │
│  App calls localhost:11434/api/generate                          │
│  Best for: faster inference, sharing with friends                │
│                                                                  │
│  OPTION C: HuggingFace Spaces (Public)                           │
│  Push Streamlit app to HF Spaces                                 │
│  Model loaded via HF Inference API                               │
│  Best for: public-facing portfolio demo                          │
│                                                                  │
│  OPTION D: Docker (Reproducible)                                 │
│  docker-compose up → full stack in containers                    │
│  Best for: sharing reproducible setup with recruiters            │
└──────────────────────────────────────────────────────────────────┘
```

---

*This document is the engineering spec. For the philosophical framework, read PHANTOM.md. For the research context, read README.md. For hardware costs, read BUDGET.md.*
