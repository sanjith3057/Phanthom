# SKILLS.md
## PHANTOM-3B Capability Registry

> *"Kakashi copies and adapts any technique. PHANTOM's skill system does the same."*

This file is the registry of all skills available in the PHANTOM-3B system. Each skill is a documented, modular capability with a corresponding `SKILL.md` in the `skills/` directory.

---

## 1. Skill Index

| Skill | Location | Status | Priority |
|---|---|---|---|
| Model Merging | skills/model-merging/SKILL.md | ✓ Active | Core |
| Benchmarking | skills/benchmarking/SKILL.md | ✓ Active | Core |
| Frontend (Streamlit) | skills/frontend/SKILL.md | ✓ Active | Core |
| Reasoning (Forge) | skills/reasoning/SKILL.md | ✓ Active | Core |

---

## 2. Skill Activation Protocol

PHANTOM reads the relevant `SKILL.md` before executing any task that belongs to that skill domain. This mirrors the CLAUDE.md skill system pattern.

```
User request arrives
      │
      ▼
FORUM Phase O (Observe):
  - Classify task into skill domain
  - Load relevant SKILL.md into context
  - Apply skill-specific best practices
      │
      ▼
FORUM Phase R (Reason):
  - Execute task with skill context active
```

### Domain Classification

```
"merge two models" / "combine weights" / "SLERP" / "TIES"
    → Load: skills/model-merging/SKILL.md

"benchmark" / "evaluate" / "score" / "compare models"
    → Load: skills/benchmarking/SKILL.md

"Streamlit" / "UI" / "interface" / "app" / "demo"
    → Load: skills/frontend/SKILL.md

"reason" / "think step by step" / "chain of thought" / "Forge"
    → Load: skills/reasoning/SKILL.md

Mixed domain:
    → Load all relevant SKILL.md files
```

---

## 3. Inherited Skills (from Prior Projects)

PHANTOM-3B inherits capabilities from the broader *Operation: Get Noticed* portfolio:

| Capability | Source Project | Files Used |
|---|---|---|
| PromptShield security | FORGE | security_guard.py |
| ReAct error recovery | GUARDIAN-AGENT | forge_reasoning.py retry logic |
| RAG-style web retrieval | PRISM-RAG | web_search.py |
| QLoRA awareness | FORGE | context for merge decisions |
| Multimodal pipeline | LENS | Future PHANTOM-VL |

---

## 4. Adding New Skills

To add a new skill to PHANTOM:

1. Create `skills/<skill-name>/SKILL.md`
2. Document: purpose, when to use, how to use, examples, pitfalls
3. Add an entry to this file (SKILLS.md)
4. Add domain classification rule to FORUM Phase O
5. Test: does PHANTOM use the skill correctly on 3 example queries?

**Skill file template:**

```markdown
# SKILL.md — [Skill Name]
## When to Use
## Core Technique
## Implementation Pattern
## Examples
## Common Pitfalls
## Connection to PHANTOM Layers
```

---

*SKILLS.md is the Kakashi scroll. Every technique PHANTOM has learned lives here.*
