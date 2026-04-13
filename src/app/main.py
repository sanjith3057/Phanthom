import sys
import os

# --- PATH FIX: Ensure src/app modules are importable when run via streamlit ---
APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

import streamlit as st
import time
import torch
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import gc
try:
    from peft import PeftModel, PeftConfig
    PEFT_AVAILABLE = True
except ImportError:
    PEFT_AVAILABLE = False

from database import init_db, save_message, get_history
from command_handler import JarvisCommandHandler
from tool_executor import ToolExecutor
from security_guard import SecurityGuard
from forge_reasoning import ForgeEngine
from utils import format_system_prompt, count_tokens
from web_search import smart_search

# --- UTILITY: TOKEN COUNTING (Redundant fallback to prevent NameErrors) ---
def count_tokens(text: str) -> int:
    try:
        import tiktoken
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except Exception:
        return max(1, len(text) // 4)

# --- SYSTEM INITIALIZATION ---
init_db()
cmd_handler = JarvisCommandHandler()
tool_exec = ToolExecutor()
security = SecurityGuard()

# --- STREAMLIT CONFIG ---
st.set_page_config(
    page_title="PHANTOM-3B | JARVIS Interface",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="⚡"
)

# --- MODEL LOADING ---
@st.cache_resource(show_spinner=False)
def load_llm_pipeline(model_path: str):
    if model_path == "Mock Engine (UI Testing)":
        return None
    
    # Aggressive memory flush
    gc.collect()
    torch.cuda.empty_cache()
    
    try:
        is_peft = os.path.exists(os.path.join(model_path, "adapter_config.json"))
        base_model_path = model_path
        
        if is_peft and PEFT_AVAILABLE:
            # For PHANTOM, the base for the aligned adapter is phantom-slerp
            base_model_path = "outputs/phantom-slerp"
            print(f"Loading PEFT adapter from {model_path} over {base_model_path}")
        
        tokenizer = AutoTokenizer.from_pretrained(base_model_path, trust_remote_code=True, use_fast=False)
        quant_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            llm_int8_enable_fp32_cpu_offload=True
        )
        
        model = AutoModelForCausalLM.from_pretrained(
            base_model_path,
            device_map="auto",
            quantization_config=quant_config,
            trust_remote_code=True
        )
        
        if is_peft and PEFT_AVAILABLE:
            model = PeftModel.from_pretrained(model, model_path)
            print("Successfully merged PEFT adapter into base model.")

        return pipeline(
            "text-generation", 
            model=model, 
            tokenizer=tokenizer, 
            max_new_tokens=1024, 
            return_full_text=False,
            do_sample=False,
            repetition_penalty=1.1,
            stop_strings=[
                "User:", "USER:", "PHANTOM:", "<|endoftext|>", "Explanation of",
                "Understanding My", "Limitations Due", "Let me break", "As a language model",
                "}"
            ]
        )
    except Exception as e:
        return {"error": str(e)}

# --- CUSTOM CSS: STARK CARBON (PHASE 3) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    /* ─── Root Tokens (Light Theme) ───────────────────────── */
    :root {
        --bg-page:      #FAFAFA;
        --bg-sidebar:   #FFFFFF;
        --bg-card:      #FFFFFF;
        --accent-cyan:  #0284C7;
        --accent-blue:  #3B82F6;
        --text-main:    #0F172A;
        --text-dim:     #64748B;
        --border:       #E2E8F0;
        --glass:       rgba(255, 255, 255, 0.8);
    }

    /* ─── Global Reset ─────────────────────────────────────── */
    .stApp {
        background-color: var(--bg-page) !important;
        color: var(--text-main) !important;
        font-family: 'Inter', sans-serif !important;
    }

    /* ─── Sidebar (The Command Center) ───────────────────────── */
    [data-testid="stSidebar"] {
        background-color: var(--bg-sidebar) !important;
        border-right: 1px solid var(--border) !important;
        padding-top: 2rem;
    }
    
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: var(--accent-cyan) !important;
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        letter-spacing: -0.02em;
        text-transform: uppercase;
        font-size: 0.85rem !important;
        margin-bottom: 1rem;
    }

    /* ─── Metric Cards ─────────────────────────────────────── */
    [data-testid="stMetric"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        padding: 10px !important;
        transition: all 0.3s ease;
    }
    [data-testid="stMetric"]:hover {
        border-color: var(--accent-cyan) !important;
        box-shadow: 0 0 15px rgba(0, 229, 255, 0.1);
    }
    [data-testid="stMetricValue"] {
        color: var(--accent-cyan) !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 1.4rem !important;
    }
    [data-testid="stMetricLabel"] {
        color: var(--text-dim) !important;
        font-size: 0.75rem !important;
        text-transform: uppercase;
    }

    /* ─── Chat Interface ────────────────────────────────────── */
    .stChatMessage {
        background-color: transparent !important;
        border-bottom: 1px solid var(--border) !important;
        padding: 1.5rem 0 !important;
    }
    .stChatMessage:last-child {
        border-bottom: none !important;
    }
    
    /* ─── Thinking Status ──────────────────────────────────── */
    .stStatusWidget {
        background-color: var(--bg-card) !important;
        border: 1px solid var(--accent-blue) !important;
    }

    /* ─── Chat Bubbles ─────────────────────────────────────── */
    .chat-user {
        background: var(--bg-card);
        border: 1px solid var(--accent-blue);
        border-radius: 12px;
        padding: 1rem;
        margin: 10px 0;
        color: var(--text-main);
    }
    .chat-bot {
        background: var(--bg-sidebar);
        border: 1px solid var(--accent-cyan);
        border-radius: 12px;
        padding: 1rem;
        margin: 10px 0;
        color: var(--text-main);
    }

    /* ─── Custom Branding ──────────────────────────────────── */
    .st-emotion-cache-1cvow48 {
        color: var(--accent-cyan) !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR: SYSTEM CONTROLS ---
with st.sidebar:
    st.markdown("### ⚡ SYSTEM OVERRIDE")
    st.markdown("---")

    selected_model = st.selectbox(
        "Active Core:",
        options=[
            "outputs/phantom-final",
            "outputs/phantom-aligned",
            "outputs/phantom-slerp",
            "outputs/phantom-ties",
            "models/qwen",
            "models/phi",
            "Mock Engine (UI Testing)",
        ],
        help="Select which model core to power PHANTOM."
    )

    st.markdown("---")
    st.markdown("**System Metrics**")
    
    # Real VRAM check
    if torch.cuda.is_available():
        vram_used = torch.cuda.memory_allocated() / 1e9
        vram_total = torch.cuda.get_device_properties(0).total_memory / 1e9
        st.metric("VRAM", f"{vram_used:.1f} / {vram_total:.0f} GB")
        st.metric("GPU", torch.cuda.get_device_name(0)[:20])
    else:
        st.metric("VRAM", "CPU Mode")

    st.markdown("---")
    if st.button("🗑️ Clear History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")
    st.markdown("""
    **Quick Commands**
    - `.status` — System check
    - `.rest` — Cooldown status
    - `.create pdf <content>` — Generate PDF
    - `.create docx <content>` — Generate DOCX
    - `.search google <query>` — Web search
    - `.search perplexica <query>` — AI search
    """)

# --- LOAD MODEL ---
with st.spinner(f"Initializing core: {selected_model}..."):
    llm_pipe = load_llm_pipeline(selected_model)

forge = ForgeEngine(llm_pipeline=llm_pipe)

# --- UI HEADER ---
from datetime import datetime
timestamp = datetime.now().strftime("%Y.%m.%d — %H:%M:%S IST")
st.markdown(
    f"<div class='status-bar'>PHANTOM-3B | ONLINE | CORE: {selected_model} | PROTOCOL: FORUM | {timestamp}</div>",
    unsafe_allow_html=True
)
st.markdown("<div class='title-glow'>P H A N T O M — 3 B</div>", unsafe_allow_html=True)
st.markdown("<p style='color:#6366F1; letter-spacing:4px; font-size:0.85rem; font-family:JetBrains Mono,monospace; font-weight:500;'>JARVIS INTERFACE — AGENTIC REASONING SYSTEM</p>", unsafe_allow_html=True)
st.markdown("---")

# --- SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = get_history()

# --- DISPLAY HISTORY ---
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"<div class='chat-user'><b>[USER]</b>&nbsp;&nbsp;{msg['content']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='chat-bot'><b>[PHANTOM]</b>&nbsp;&nbsp;{msg['content']}</div>", unsafe_allow_html=True)

# --- CHAT INPUT ---
if prompt := st.chat_input("Enter command or query..."):
    start_time = time.time()  # Start the reasoning timer
    # Display user message immediately
    st.markdown(f"<div class='chat-user'><b>[USER]</b>&nbsp;&nbsp;{prompt}</div>", unsafe_allow_html=True)
    st.session_state.messages.append({"role": "user", "content": prompt})
    save_message("user", prompt)

    # Step 1: Check dot-commands (bypass LLM entirely)
    cmd_result = cmd_handler.process_command(prompt)
    if cmd_result:
        st.markdown(f"<div class='chat-bot'><b>[PHANTOM]</b>&nbsp;&nbsp;{cmd_result}</div>", unsafe_allow_html=True)
        st.session_state.messages.append({"role": "assistant", "content": cmd_result})
        save_message("assistant", cmd_result)
        st.stop()

    # Step 2: Rate limit check
    is_allowed, rem_time = cmd_handler.rate_limiter.check_cooldown()
    if not is_allowed:
        rest_msg = f"⏳ System calibration in progress. Hold for {rem_time}s."
        st.markdown(f"<div class='chat-bot'><b>[PHANTOM]</b>&nbsp;&nbsp;{rest_msg}</div>", unsafe_allow_html=True)
        st.session_state.messages.append({"role": "assistant", "content": rest_msg})
        save_message("assistant", rest_msg)
        st.stop()

    cmd_handler.rate_limiter.record_interaction()

    # Step 3: Security filter (Phase F)
    is_safe, sec_msg = security.check_input(prompt)
    if not is_safe:
        st.error(f"🚫 {sec_msg}")
        st.stop()

    # Step 4: Forge reasoning (Phase R)
    system_prompt = format_system_prompt([])
    complexity = forge.assess_complexity(prompt)

    # Intelligent Context Management (KV-Preservation Protocol)
    history_messages = st.session_state.messages.copy()
    while len(history_messages) > 1:
        current_ctx = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in history_messages])
        if count_tokens(current_ctx) < 1000:
            break
        history_messages.pop(0)
    
    history_ctx = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in history_messages])

    with st.spinner("🧠 Reasoning via FORUM Protocol..."):
        # --- PHASE S: Autonomous Technical Search ---
        search_data = None
        if forge.is_technical_query(prompt):
            st.toast("🌐 Omniscience Active: Searching technical specs...", icon="🔍")
            search_data = smart_search(prompt)
            if "Error" in search_data or "not reachable" in search_data:
                st.warning("⚠️ Web search unavailable. Falling back to local Architecture Heuristics.")
                search_data = None

        if complexity == "forge":
            # --- MICRO-TASKING PASS 1: Architect ---
            st.toast("Phase A: Architecting logic...", icon="🏗️")
            architect_prompt = f"TASK: Architect the structure for this query. Identify components and logic only. Use the provided SEARCH DATA to ensure technical accuracy.\n\nQuery: {prompt}"
            structure = forge.reason(system_prompt, history_ctx, architect_prompt, search_data=search_data)
            
            # --- MICRO-TASKING PASS 2: Coder/Finalizer ---
            st.toast("Phase B: Generating final implementation...", icon="💻")
            coder_prompt = f"TASK: Using the following architecture, provide the final detailed implementation and response.\n\nArchitecture:\n{structure}\n\nQuery: {prompt}"
            llm_response = forge.reason(system_prompt, history_ctx, coder_prompt, search_data=search_data)
        else:
            # Single-pass with search data injection
            llm_response = forge.reason(system_prompt, history_ctx, prompt, search_data=search_data)
    
    # --- HARD TRUNCATION: Kill Wall-of-Text Drift ---
    bad_markers = [
        "User:", "USER:", "PHANTOM:", "Note:", "Explanation:", "Assistant:", 
        "\n{", "\n[", "\n---", "Understanding My", "Limitations Due", "Let me break"
    ]
    for marker in bad_markers:
        if marker in llm_response:
            llm_response = llm_response.split(marker)[0].strip()

    # Step 5: Output review (Phase U)
    out_safe, clean_response = security.review_output(llm_response)
    if not out_safe:
        st.error(f"🚫 {clean_response}")
        st.stop()

    # --- REASONING LATENCY TRACKING ---
    latency = time.time() - start_time
    st.session_state.last_latency = latency

    # --- DISPLAY RESPONSE ---
    with st.chat_message("assistant", avatar="⚡"):
        st.markdown(llm_response)
        
        # --- PHASE 3: TECHNICAL SCRUTINY EXPANDER ---
        with st.expander("🛠️ TECHNICAL SCRUTINY (DETERMINISTIC DATA)"):
            st.markdown("**Live Specifications (Omniscience):**")
            st.code(search_data if search_data else "No live search performed.")
            
            st.markdown("**Knowledge Map Facts:**")
            facts = forge.search_knowledge_map(prompt)
            st.code(facts)
            
            st.caption(f"Reasoning Latency: {latency:.2f}s | Context: {count_tokens(llm_response)} tokens")

    # Save to history
    st.session_state.messages.append({"role": "assistant", "content": llm_response})
    save_message("assistant", llm_response)

    # Step 6: Tool detection & execution
    tool_triggered, final_content = tool_exec.detect_and_execute(clean_response)

    # Step 7: Render and persist
    st.markdown(f"<div class='chat-bot'><b>[PHANTOM]</b>&nbsp;&nbsp;{final_content}</div>", unsafe_allow_html=True)
    st.session_state.messages.append({"role": "assistant", "content": final_content})
    save_message("assistant", final_content)
