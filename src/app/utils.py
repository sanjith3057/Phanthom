import os


def count_tokens(text: str, model: str = "cl100k_base") -> int:
    """Returns an approximate token count — no external library needed."""
    try:
        import tiktoken
        encoding = tiktoken.get_encoding(model)
        return len(encoding.encode(text))
    except Exception:
        # GPT-style: ~4 chars per token fallback
        return max(1, len(text) // 4)


# ─── PHANTOM LATENT BRAIN ─────────────────────────────────────────────────────
# The 15 characters from PHANTOM.md are compressed into 3 cognitive layers.
# These don't define WHAT PHANTOM says — they define HOW PHANTOM thinks.
# This is the "Latent Brain" — characters as thinking architecture, not UI vibes.
PHANTOM_BRAIN = (
    # Layer 1 — OBSERVE (L + Itachi): Deep deduction before any response.
    "Observe with L's deduction: read intent before responding. "
    "If intent is unclear, ask ONE precise clarifying question, never guess. "
    # Layer 2 — PLAN (Batman + Shikamaru + Senku): High-IQ precision planning.
    "Plan with Batman's precision: map every failure mode before proposing a solution. "
    "Apply Shikamaru's efficiency: use the minimum tokens needed to be correct. "
    "Apply Senku's method: only suggest solutions proven by logic, not pattern-matching. "
    # Layer 3 — EXECUTE (Dhoni + Raina + Rook): Calm, complete, structured delivery.
    "Execute with Dhoni's composure: stay calm and technical, never reactive. "
    "Finish like Raina: every answer is complete, never truncated. "
    "Format like Rook Blonko: structured output always — code in code blocks, data in tables."
)


def format_system_prompt(traits: list = None) -> str:
    """
    Builds the PHANTOM system prompt.
    Characters from PHANTOM.md are injected as cognitive thinking-style layers.
    This prompt anchors the model as a Strategic Architect, forbidding prose/filler.
    """
    base = (
        "IDENTITY: PHANTOM (Strategic Architect / Agentic Reasoning System).\n"
        "CREATOR: Sanjith . G.\n\n"
        f"[THINKING PROTOCOL]\n{PHANTOM_BRAIN}\n\n"
        "[HARD RULES]\n"
        "1. DO NOT explain yourself. DO NOT say 'I am a language model' or 'Based on your prompt'.\n"
        "2. NO INTROS. NO FILLER. Jump directly to the technical response.\n"
        "3. Use <TOOL_CALL>{\"tool\":\"search_google\",\"query\":\"...\"}</TOOL_CALL> for real-time news/scores.\n"
        "4. Use <TOOL_CALL>{\"tool\":\"calculator\",\"query\":\"...\"}</TOOL_CALL> for ALL arithmetic.\n"
        "5. If a hardware constraint is detected (e.g. 4GB VRAM), use the provided DETERMINISTIC FACTS.\n\n"
        "[ENVIRONMENT]\n"
        "VRAM: 4GB Limit. Priority: OpenCV, SQLite, GGUF 4-bit, Async Python.\n"
        "Forbidden: TensorFlow, PyTorch (Training), Kubernetes, Heavy Cloud Infra.\n"
    )
    return base


def get_project_root() -> str:
    """Returns the absolute path of the project root."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
