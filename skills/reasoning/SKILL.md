# SKILL.md — Forge Multi-Reasoning Engine
## Chain-of-Thought, Tree-of-Thought & Self-Consistency for PHANTOM

> *Inherited and extended from the FORGE project. This is PHANTOM's core reasoning layer.*

---

## When to Use This Skill

Use the Forge reasoning engine when:
- The query requires multi-step problem solving
- A single pass at the question is likely to produce errors
- You need a confidence score on the output
- The user explicitly asks for step-by-step thinking

Skip to direct generation when:
- Query is simple factual lookup
- Query is single-step (one arithmetic operation, one format conversion)
- Token budget is critically low

---

## The Three Paths

### Path A: Chain of Thought (CoT)

**What it does:** Forces the model to articulate its reasoning before committing to an answer. Reduces errors on multi-step problems by making intermediate steps explicit.

**When to use:** Linear problems with a clear sequence of steps. Math word problems, logical deductions, code with multiple sub-problems.

**Implementation:**

```python
COT_SYSTEM = """Think through this step by step. Show your reasoning.
Do not skip steps. Arrive at your final answer only after reasoning through it."""

COT_TEMPLATE = """
Problem: {question}

Let me think through this step by step:

Step 1:"""

def chain_of_thought(model, tokenizer, question: str) -> tuple[str, str]:
    """
    Returns (reasoning_trace, final_answer)
    Extract final answer from after the last "Therefore:" or "Answer:" marker.
    """
    prompt = COT_TEMPLATE.format(question=question)
    response = generate(model, tokenizer, prompt)

    # Extract final answer
    for marker in ["Therefore:", "Answer:", "Final answer:", "Result:"]:
        if marker in response:
            final_answer = response.split(marker)[-1].strip()
            return response, final_answer

    # Fallback: last paragraph
    return response, response.split('\n\n')[-1].strip()
```

---

### Path B: Tree of Thought (ToT)

**What it does:** Generates multiple competing solution approaches, evaluates each, and selects the best path. Models a search over solution space rather than a linear walk.

**When to use:** Optimization problems, questions with multiple valid framings, creative tasks where one approach might miss the point.

**Implementation:**

```python
TOT_TEMPLATE = """
Problem: {question}

I will consider three different approaches:

Approach A: [Most direct method]
{approach_a}

Approach B: [Alternative framing]
{approach_b}

Approach C: [Edge-case aware method]
{approach_c}

Evaluation:
- Approach A: [pros/cons]
- Approach B: [pros/cons]
- Approach C: [pros/cons]

Best approach: [Approach X] because [reason]

Final answer using best approach:"""

def tree_of_thought(model, tokenizer, question: str) -> tuple[str, str]:
    """
    Generate 3 approaches then select best.
    Returns (full_tree, selected_answer)
    """
    # Phase 1: Generate approaches
    approach_prompt = f"List 3 different approaches to solve this: {question}"
    approaches = generate(model, tokenizer, approach_prompt)

    # Phase 2: Evaluate and select
    eval_prompt = TOT_TEMPLATE.format(
        question=question,
        approach_a=extract_approach(approaches, 'A'),
        approach_b=extract_approach(approaches, 'B'),
        approach_c=extract_approach(approaches, 'C'),
    )
    full_tree = generate(model, tokenizer, eval_prompt)

    # Extract selected answer
    final = extract_section(full_tree, "Final answer using best approach:")
    return full_tree, final
```

---

### Path C: Self-Consistency (SC)

**What it does:** Generates N independent responses to the same question (with slight temperature > 0), then votes on the most common final answer. Mimics the "wisdom of crowds" effect within a single model.

**When to use:** Questions with a single correct answer where the model is uncertain. Works especially well for reasoning and math where there is one ground truth.

**Implementation:**

```python
def self_consistency(
    model, tokenizer, question: str,
    n: int = 3,
    temperature: float = 0.3
) -> tuple[str, float]:
    """
    Generate n responses → extract final answers → vote → return majority.
    Returns (winning_answer, confidence) where confidence = votes/n
    """
    responses = []
    answers = []

    for _ in range(n):
        response = generate(
            model, tokenizer, question,
            temperature=temperature,
            do_sample=True
        )
        responses.append(response)
        answers.append(extract_final_answer(response))

    # Normalize answers for comparison
    normalized = [normalize_answer(a) for a in answers]

    # Find majority
    from collections import Counter
    vote_counts = Counter(normalized)
    winning_answer, winning_votes = vote_counts.most_common(1)[0]
    confidence = winning_votes / n

    # Return the original (non-normalized) version of winning answer
    winning_idx = normalized.index(winning_answer)
    return answers[winning_idx], confidence
```

---

## Complexity Router

The router decides which path(s) to use based on the input complexity score.

```python
def compute_complexity(prompt: str) -> float:
    """
    Returns 0.0 (simple) to 1.0 (complex).
    Composite of: length, constraint count, multi-step signals.
    """
    score = 0.0

    # Length component (0.0 – 0.3)
    words = len(prompt.split())
    score += min(words / 100, 1.0) * 0.3

    # Constraint count (0.0 – 0.4)
    constraint_words = ['exactly', 'must', 'only', 'never', 'always',
                        'without', 'before', 'after', 'each', 'every']
    constraint_count = sum(1 for w in constraint_words if w in prompt.lower())
    score += min(constraint_count / 5, 1.0) * 0.4

    # Multi-step signals (0.0 or 0.3)
    multi_step_phrases = ['step by step', 'then', 'after that', 'first',
                          'finally', 'next', 'how many', 'prove', 'derive']
    if any(p in prompt.lower() for p in multi_step_phrases):
        score += 0.3

    return min(score, 1.0)


def route_reasoning(prompt: str) -> str:
    """
    Route to appropriate reasoning path.
    Returns: 'direct' | 'cot' | 'tot' | 'sc_cot'
    """
    score = compute_complexity(prompt)

    if score < 0.4:
        return 'direct'       # Simple → direct generation
    elif score < 0.65:
        return 'cot'          # Medium → chain of thought
    elif score < 0.85:
        return 'tot'          # Complex → tree of thought
    else:
        return 'sc_cot'       # Very complex → self-consistency over CoT
```

---

## Confidence Gating

After any reasoning path, a confidence gate decides whether to return the answer or request clarification.

```python
CONFIDENCE_THRESHOLD = 0.6

def confidence_gate(answer: str, confidence: float, path: str) -> ReasoningResult:
    """
    If confidence is low, flag the answer for review rather than delivering it silently.
    """
    if confidence >= CONFIDENCE_THRESHOLD:
        return ReasoningResult(
            answer=answer,
            confidence=confidence,
            path=path,
            status='delivered'
        )
    else:
        # Low confidence — deliver with caveat
        caveat = (
            f"\n\n[PHANTOM note: confidence on this answer is {confidence:.0%}. "
            f"You may want to verify this independently.]"
        )
        return ReasoningResult(
            answer=answer + caveat,
            confidence=confidence,
            path=path,
            status='delivered_with_caveat'
        )
```

---

## Token Budget Enforcement (Shikamaru Layer)

```python
class BudgetAwareReasoner:
    """
    Wraps ForgeReasoningEngine with token budget enforcement.
    If budget is low, skip expensive paths.
    """
    def __init__(self, engine: ForgeReasoningEngine, budget: TokenBudget):
        self.engine = engine
        self.budget = budget

    def reason(self, prompt: str) -> ReasoningResult:
        path = route_reasoning(prompt)
        estimated_tokens = estimate_tokens(prompt, path)

        # Override path if budget is insufficient
        if self.budget.remaining < estimated_tokens:
            if path in ['tot', 'sc_cot']:
                path = 'cot'   # Downgrade to cheaper path
            if self.budget.remaining < 200:
                path = 'direct'  # Critically low — go direct

        return self.engine.reason(prompt, force_path=path)
```

---

## Integration with PHANTOM-3B Model

The Forge reasoning engine calls PHANTOM's merged model for generation:

```python
# In forge_reasoning.py

from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

class PHANTOMModel:
    def __init__(self, model_path: str, device: str = "cuda"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.bfloat16,
            device_map=device
        )

    def generate(self, prompt: str, **kwargs) -> str:
        # Apply chat template
        messages = [{"role": "user", "content": prompt}]
        formatted = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        inputs = self.tokenizer(formatted, return_tensors="pt").to(self.model.device)
        output = self.model.generate(**inputs, **kwargs)
        return self.tokenizer.decode(output[0][inputs['input_ids'].shape[1]:],
                                     skip_special_tokens=True)
```

---

## Performance Characteristics

```
Path         Avg Tokens Used   Avg Latency (RTX 2050)   Best For
──────────────────────────────────────────────────────────────────
direct       ~100 output       ~2 sec                   Simple queries
cot          ~300 output       ~5 sec                   Math, logic
tot          ~600 output       ~12 sec                  Multi-approach
sc_cot(n=3)  ~900 output       ~15 sec                  Max accuracy
```

---

## Connection to PHANTOM Characters

| Reasoning Path | Character | Trait Expressed |
|---|---|---|
| CoT | Senku | Build from first principles, step by step |
| ToT | Batman | Consider all angles before committing |
| Self-Consistency | L | Run independent deductions, find the truth |
| Complexity Router | Shikamaru | Don't overthink the easy ones |
| Confidence Gate | Itachi | Silent observation — don't speak until certain |
| Completion | Raina | Always finish. Hit the boundary. |
