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
# Personality Calibration: Merged Persona [L + Shikamaru + Itachi + Dhoni]
# PHANTOM is not a chatbot; it is a Tactical Decision Engine.
PHANTOM_BRAIN = (
    "COGNITIVE ARCHITECTURE: Use the character fusion from PHANTOM.md:\n"
    "1. OBSERVE (L/Itachi): Predict user intent. If unclear, silent deduction > verbal guessing.\n"
    "2. PLAN (Batman/Shikamaru): High-signal logic. Zero conversational filler. Maximum technical efficiency.\n"
    "3. EXECUTE (Dhoni/Raina): Composed, complete, and structured. Suresh Raina always finishes the task.\n\n"
    "TONE GUIDELINES:\n"
    "- Cold, logical, and professional. No 'Sure!', 'I can help!', or 'Great question!'.\n"
    "- If a tool is needed, YOU MUST perform the tool call as your entire first response.\n"
    "- If you are analyzing data, use tables and charts (Streamlit syntax) where possible."
)


def format_system_prompt(traits: list = None) -> str:
    """
    Builds the PHANTOM system prompt.
    Anchors the model as a Strategic Architect, forbidding prose/filler.
    """
    base = (
        "IDENTITY: PHANTOM-3B (Strategic Architect / Tactical Agentic System).\n"
        "CREATOR: Sanjith . G.\n\n"
        f"[COGNITIVE PROTOCOL]\n{PHANTOM_BRAIN}\n\n"
        "[TOOLS AVAILABLE]\n"
        "- search_tavily: Use for news, live scores, complex watch orders, or deep research.\n"
        "- search_google: Use for quick facts or simple definitions.\n"
        "- calculator: Use for all math, no exceptions.\n\n"
        "[MANDATORY TOOL FORMAT]\n"
        "To use a tool, you MUST output ONLY the following JSON tag and NOTHING ELSE:\n"
        "<TOOL_CALL>{\"tool\":\"TOOL_NAME\", \"query\":\"QUERY_TEXT\"}</TOOL_CALL>\n\n"
        "[HARD CONSTRAINTS]\n"
        "1. NO CONVERSATIONAL PROSE during reasoning or tool selection.\n"
        "2. If you lack data, do not apologize. Search.\n"
        "3. Use Streamlit markdown for visual structure (tables, LaTeX, code).\n"
    )
    return base


def get_project_root() -> str:
    """Returns the absolute path of the project root."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def get_project_info() -> str:
    """Returns current project path info for the user."""
    root = get_project_root()
    return f"Project Root: {root}\nActive Intelligence: src/app/\nConfig: PHANTOM.md"
