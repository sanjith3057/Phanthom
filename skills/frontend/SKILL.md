# SKILL.md — Frontend (Streamlit)
## Professional UI Patterns for PHANTOM-3B

---

## When to Use This Skill

Use this skill when building or modifying:
- `src/app/main.py` (main Streamlit app)
- Any new page or component within the Streamlit interface
- The benchmark dashboard visualization
- The chat interface and model selector

---

## Core Design Principles (PHANTOM Aesthetic)

PHANTOM's UI is **dark, minimal, and high-signal**. It reflects the personality: calm, structured, no noise.

```
Color Palette:
  Background:     #0a0a0a  (near-black)
  Surface:        #141414  (card backgrounds)
  Border:         #2a2a2a  (subtle separators)
  Accent:         #7c3aed  (PHANTOM purple — active elements)
  Accent hover:   #6d28d9
  Text primary:   #f5f5f5  (high contrast)
  Text secondary: #9ca3af  (metadata, labels)
  Success:        #10b981  (benchmark wins)
  Warning:        #f59e0b  (partial scores)
  Error:          #ef4444  (zero scores)
```

---

## Streamlit Custom Styling

Place in `static/css/custom.css` and inject via `st.markdown`:

```python
def inject_styles():
    with open("static/css/custom.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
```

```css
/* static/css/custom.css */

/* Global */
.stApp {
    background-color: #0a0a0a;
    color: #f5f5f5;
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
}

/* Sidebar */
.css-1d391kg {
    background-color: #141414;
    border-right: 1px solid #2a2a2a;
}

/* Chat message bubbles */
.user-message {
    background: #1e1e2e;
    border-left: 3px solid #7c3aed;
    padding: 12px 16px;
    border-radius: 0 8px 8px 0;
    margin: 8px 0;
}

.assistant-message {
    background: #141414;
    border-left: 3px solid #10b981;
    padding: 12px 16px;
    border-radius: 0 8px 8px 0;
    margin: 8px 0;
}

/* Token budget bar */
.budget-bar {
    height: 4px;
    background: linear-gradient(90deg, #7c3aed, #10b981);
    border-radius: 2px;
}

/* Benchmark table — win highlight */
.score-win {
    color: #10b981;
    font-weight: bold;
}

.score-lose {
    color: #9ca3af;
}
```

---

## Page Architecture

### Page 1: Home

```python
def page_home():
    st.title("PHANTOM-3B")
    st.caption("A merged language model: Qwen2.5-3B × Phi-3.5-mini")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Merge Method", "TIES + DARE")
    with col2:
        st.metric("Benchmark Score", "8/10")
    with col3:
        st.metric("vs Parents", "+2 over best")

    st.markdown("---")

    # Model card preview
    with st.expander("What is PHANTOM-3B?"):
        st.markdown("""
        PHANTOM-3B is the geometric midpoint between two specialists:
        - **Qwen2.5-3B-Instruct** → reasoning & instruction following
        - **Phi-3.5-mini-instruct** → coding & structured output

        Created via SLERP and TIES+DARE merging using MergeKit.
        No training data. No fine-tuning. 20 minutes on consumer hardware.
        """)

    st.link_button("View on HuggingFace", "https://huggingface.co/YOUR_USERNAME/phantom-3b")
```

---

### Page 2: Chat Interface

```python
def page_chat():
    st.title("Chat with PHANTOM")

    # Sidebar controls
    with st.sidebar:
        model_choice = st.radio(
            "Model",
            ["phantom-ties (recommended)", "phantom-slerp"],
            index=0
        )
        reasoning_mode = st.select_slider(
            "Reasoning depth",
            options=["direct", "chain-of-thought", "tree-of-thought", "full-forge"],
            value="chain-of-thought"
        )
        web_search = st.toggle("Enable web search", value=False)

        # Token budget meter
        st.markdown("**Token budget**")
        budget_used = st.session_state.get('tokens_used', 0)
        budget_total = 4096
        progress = budget_used / budget_total
        st.progress(progress)
        st.caption(f"{budget_used} / {budget_total} tokens")

    # Chat history from SQLite
    messages = db.get_messages(st.session_state.session_id)
    for msg in messages:
        with st.chat_message(msg['role']):
            st.markdown(msg['content'])

    # Input
    if prompt := st.chat_input("Ask PHANTOM anything..."):
        # Security check (Phase F)
        if security_guard.check(prompt)['blocked']:
            st.error("That request was blocked by PromptShield.")
            return

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response (Forge reasoning)
        with st.chat_message("assistant"):
            with st.spinner("PHANTOM is reasoning..."):
                result = forge_engine.reason(prompt)
            st.markdown(result.answer)

            # Show reasoning path (optional)
            if reasoning_mode != "direct":
                with st.expander(f"Reasoning path: {result.path}"):
                    st.code(result.reasoning_trace)
```

---

### Page 3: Benchmark Dashboard

```python
def page_benchmark():
    st.title("Benchmark Dashboard")
    st.caption("4 models × 10 questions × 3 categories")

    # Load benchmark data
    data = load_benchmark_results()

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    cols = [col1, col2, col3, col4]
    for i, (model_name, scores) in enumerate(data.items()):
        with cols[i]:
            is_winner = model_name == 'phantom-ties'
            delta = scores['total'] - data['qwen']['total']
            st.metric(
                label=model_name,
                value=f"{scores['total']}/10",
                delta=f"+{delta}" if delta > 0 else str(delta),
                delta_color="normal" if is_winner else "off"
            )

    st.markdown("---")

    # Category breakdown (bar chart)
    import plotly.graph_objects as go
    fig = go.Figure(data=[
        go.Bar(name='Reasoning', x=list(data.keys()),
               y=[v['reasoning'] for v in data.values()], marker_color='#7c3aed'),
        go.Bar(name='Coding', x=list(data.keys()),
               y=[v['coding'] for v in data.values()], marker_color='#10b981'),
        go.Bar(name='Instruction', x=list(data.keys()),
               y=[v['instruction'] for v in data.values()], marker_color='#f59e0b'),
    ])
    fig.update_layout(
        barmode='group',
        paper_bgcolor='#0a0a0a',
        plot_bgcolor='#141414',
        font_color='#f5f5f5',
    )
    st.plotly_chart(fig, use_container_width=True)

    # Money shot — the question PHANTOM wins uniquely
    st.markdown("### The Win")
    st.markdown("*The question where PHANTOM beats both parents:*")
    money_shot = find_money_shot(data)
    if money_shot:
        st.info(money_shot['question'])
        cols = st.columns(4)
        for i, (model, score) in enumerate([
            ('qwen', money_shot['qwen']),
            ('phi', money_shot['phi']),
            ('phantom-slerp', money_shot.get('slerp', 0)),
            ('phantom-ties ★', money_shot['phantom'])
        ]):
            with cols[i]:
                color = "green" if model == 'phantom-ties ★' else "normal"
                st.metric(model, f"{score}/1.0")
```

---

## State Management

```python
# Initialize session state at app startup
def init_session():
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
        db.create_session(st.session_state.session_id)

    if 'tokens_used' not in st.session_state:
        st.session_state.tokens_used = 0

    if 'model_loaded' not in st.session_state:
        # Load model once, cache in session state
        st.session_state.model = PHANTOMModel('./outputs/phantom-ties')
        st.session_state.model_loaded = True
```

---

## Performance Optimization

```python
# Cache model loading — don't reload on every rerun
@st.cache_resource
def load_model(model_path: str):
    return PHANTOMModel(model_path)

# Cache benchmark results — don't recompute on every rerun
@st.cache_data
def load_benchmark_results():
    import json
    results = {}
    for model in ['qwen', 'phi', 'phantom-slerp', 'phantom-ties']:
        path = f"outputs/benchmark_{model}.json"
        if os.path.exists(path):
            with open(path) as f:
                results[model] = json.load(f)
    return results
```

---

## Connection to PHANTOM Layers

This skill activates in:
- **Phase M (Memory → UI):** Streamlit is the surface where session memory is displayed
- **Layer 5 (Raina — The Finisher):** The UI is the final delivery mechanism. No trailing off. The chat interface renders complete answers, the benchmark dashboard tells the complete story.
