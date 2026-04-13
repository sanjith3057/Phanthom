# PRODUCT.md
## PHANTOM-3B — Product Roadmap & Sprint Planning

> *"Madara manages the war. Ruturaj stays consistent. Raina finishes."*

---

## 1. Product Vision

PHANTOM-3B is not just a portfolio project. It is the proof-of-concept for a product hypothesis:

**Hypothesis:** A merged 3B model with a well-designed reasoning layer can outperform either of its parent models on a combined multi-domain benchmark — and can be built, documented, and shipped in a single working day on consumer hardware.

**If proven true**, this demonstrates:
1. Model merging is underutilized by the ML community
2. Capability composition without training is real and reproducible
3. The builder understands weight-space geometry, not just API calls

---

## 2. Current Sprint — Week 2, Day 1

### Sprint Goal

Build PHANTOM-3B (merged model) + benchmark it against both parents + publish to HuggingFace + ship Streamlit demo.

### Sprint Deliverables

```
╔══════════════════════════════════════════════════════════════╗
║             WEEK 2, DAY 1 — DELIVERABLES CHECKLIST          ║
╠══════════════════════════════════════════════════════════════╣
║  ☐ PHANTOM-SLERP merged model (outputs/phantom-slerp/)      ║
║  ☐ PHANTOM-TIES merged model  (outputs/phantom-ties/)        ║
║  ☐ Benchmark JSON files (all 4 models)                      ║
║  ☐ Comparison table (outputs/comparison_table.md)           ║
║  ☐ HuggingFace model published (with model card)            ║
║  ☐ Streamlit demo running locally (src/app/main.py)          ║
║  ☐ GitHub repo pushed (with full README)                    ║
║  ☐ LinkedIn post published                                  ║
╚══════════════════════════════════════════════════════════════╝
```

---

## 3. Operation: Get Noticed — 30-Day Sprint Context

PHANTOM-3B is Day 1 of Week 2 in the broader "Operation: Get Noticed" sprint.

```
WEEK 1 — COMPLETED
├── Day 1:  PRISM-RAG     (5-layer RAG solving lost-in-the-middle)
├── Day 2:  GUARDIAN-AGENT (self-healing ReAct agent)
├── Day 3:  LENS           (multimodal doc intelligence, CLIP + Qwen2-VL)
└── Day 4:  FORGE          (QLoRA fine-tuning for 4GB VRAM)

WEEK 2 — IN PROGRESS
├── Day 1:  PHANTOM-3B ← YOU ARE HERE
├── Day 2:  [TBD — likely MLOps / deployment project]
├── Day 3:  [TBD]
└── Day 4:  [TBD]
```

### Portfolio Narrative Arc

Each project in the sprint tells a chapter of the same story:

```
PRISM-RAG       → "I can build production RAG pipelines"
GUARDIAN-AGENT  → "I can build self-healing agentic systems"
LENS            → "I can work with multimodal AI"
FORGE           → "I can fine-tune models on limited hardware"
PHANTOM-3B      → "I can create models, not just use them"
```

PHANTOM-3B is the peak of the arc — the most technically unusual and the most differentiated from what recruiters typically see.

---

## 4. Roadmap — Future PHANTOM Versions

### v0.1 — PHANTOM-3B (Now)
- ✓ SLERP + TIES merge of Qwen2.5-3B + Qwen2.5-Coder-3B
- ✓ 10-question benchmark vs. parents
- ✓ Streamlit demo with Forge reasoning
- ✓ HuggingFace publish

### v0.2 — PHANTOM-3B Enhanced (Week 3, optional)
- Add PHANTOM-VL variant using LENS multimodal layer
- Extend benchmark to 25 questions across 5 categories
- Add GGUF quantization for Ollama serving
- Publish HuggingFace Space for public access

### v0.3 — PHANTOM-7B (Future, requires better hardware)
- Parent models: Qwen2.5-7B-Instruct + Phi-4-mini
- SLERP + evolutionary merge optimization
- Professional benchmark suite (MMLU subset, HumanEval subset)
- Full MLflow experiment tracking (from FORGE pipeline)

### v1.0 — PHANTOM-AGENT (Long term)
- PHANTOM-3B as the reasoning core of a full agentic system
- Integrates: PRISM-RAG (knowledge) + GUARDIAN-AGENT (reliability)
- Persistent memory across sessions
- Tool use: code execution, web search, file I/O

---

## 5. Success Metrics

```
PRIMARY METRICS (this sprint):
  ✓ PHANTOM-TIES score > Qwen parent score
  ✓ PHANTOM-TIES score > Phi parent score
  ✓ Model published on HuggingFace with model card
  ✓ GitHub commit pushed with full README
  ✓ LinkedIn post published

SECONDARY METRICS (48 hours post-publish):
  • GitHub stars: ≥ 3
  • HuggingFace downloads: ≥ 10
  • LinkedIn post impressions: ≥ 500
  • LinkedIn post reactions: ≥ 20
  • Recruiter DMs triggered: ≥ 1

FAILURE CONDITIONS:
  ✗ PHANTOM scores BELOW both parents on benchmark
     → Action: Tune t and density values, re-merge, re-benchmark
  ✗ Model does not load (OOM or corrupt weights)
     → Action: Check --allow-crimes flag, verify architecture compat
  ✗ No time to push to HuggingFace
     → Action: Push GitHub first, HuggingFace next day
```

---

## 6. Risk Registry

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Merge produces incoherent model | Medium | High | Verify sanity check after each merge before benchmarking |
| OOM during merge on 16GB RAM | Low | Medium | Use `--low-cpu-mem-usage` flag |
| PHANTOM scores worse than both parents | Medium | Medium | Tune `t` toward stronger parent on weakest category |
| HuggingFace upload slow on Indian internet | Medium | Low | Use `hf_transfer` library for faster upload |
| Benchmark questions are too easy/hard | Low | Low | Questions chosen from known model capability gaps |

---

## 7. Definition of Done

PHANTOM-3B is complete when:

1. Both merged model directories exist and load without error
2. Benchmark JSON files exist for all 4 models
3. Comparison table shows PHANTOM-TIES > both parents
4. HuggingFace URL exists with model card
5. GitHub repo is public with README, PHANTOM.md, and full docs/
6. LinkedIn post is live with HuggingFace link in comments

---

*PRODUCT.md is updated at the start of each sprint. Last updated: Week 2, Day 1.*
