import streamlit as st
from core.hf_llm import query_llm
from core import prompts
import speech_recognition as sr
from core.code_runner import run_code
from streamlit_ace import st_ace  # type: ignore
from utils.utils_ast import generate_outline, execute_instrumented_code, get_first_function_name
from utils.utils_complexity import guess_time_complexity
from utils.utils_complexity_advanced import (
    cyclomatic_complexity_report,
    generate_function_call_graph,
)
from utils.utils_complexity_generic import heuristic_time_complexity, heuristic_space_complexity, generate_complexity_graph
import re
import time
import uuid
import plotly.graph_objects as go
from gtts import gTTS
import io

# CSS is injected inside run_app() after st.set_page_config() to avoid
# duplicate rendering (set_page_config must be the very first Streamlit call).
_APP_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.main .block-container { padding: 1.5rem 2rem 2rem 2rem; max-width: 1200px; }
h1 { font-weight: 700; letter-spacing: -0.5px; }
h2 { font-weight: 600; margin-top: 0.25rem; }
h3 { font-weight: 500; }
.stTabs [data-baseweb="tab-list"] { gap: 4px; background: transparent; flex-wrap: wrap; }
.stTabs [data-baseweb="tab"] { padding: 0.55rem 1.1rem; border-radius: 8px 8px 0 0; font-size: 0.82rem; font-weight: 500; transition: background 0.2s; }
.stTabs [data-baseweb="tab"]:hover { background: rgba(100,149,237,0.15); }
.stTabs [aria-selected="true"] { font-weight: 700; border-bottom: 3px solid #4a90d9; }
.stButton > button[kind="primary"] { background: linear-gradient(135deg,#2563eb,#1d4ed8); color: white; border: none; border-radius: 8px; padding: 0.55rem 1.4rem; font-weight: 600; font-size: 0.9rem; transition: all 0.2s ease; box-shadow: 0 2px 8px rgba(37,99,235,0.35); }
.stButton > button[kind="primary"]:hover { background: linear-gradient(135deg,#1d4ed8,#1e40af); box-shadow: 0 4px 14px rgba(37,99,235,0.5); transform: translateY(-1px); }
.stButton > button[kind="secondary"] { background: rgba(100,149,237,0.12); color: #93c5fd; border: 1px solid rgba(100,149,237,0.3); border-radius: 8px; padding: 0.5rem 1.1rem; font-weight: 500; font-size: 0.88rem; transition: all 0.2s ease; }
.stButton > button[kind="secondary"]:hover { background: rgba(100,149,237,0.22); border-color: #93c5fd; transform: translateY(-1px); }
.metric-card { background: linear-gradient(135deg,rgba(37,99,235,0.12),rgba(29,78,216,0.06)); border: 1px solid rgba(37,99,235,0.25); border-left: 4px solid #2563eb; border-radius: 12px; padding: 1.1rem 1.2rem; text-align: center; transition: box-shadow 0.2s; }
.metric-card:hover { box-shadow: 0 4px 16px rgba(37,99,235,0.2); }
.empty-state { background: rgba(255,255,255,0.03); border: 1px dashed rgba(255,255,255,0.15); border-radius: 12px; padding: 2rem; text-align: center; color: rgba(255,255,255,0.45); font-size: 0.9rem; margin-top: 1rem; }
.stAlert { border-radius: 10px; }
[data-testid="stSidebar"] { background: rgba(15,20,35,0.95); border-right: 1px solid rgba(255,255,255,0.07); }
[data-testid="stSidebar"] .stButton > button { width: 100%; }
.stCodeBlock { border-radius: 10px; font-size: 0.85rem; }
hr { border-color: rgba(255,255,255,0.08) !important; margin: 1rem 0 !important; }
[data-testid="stChatMessage"] { border-radius: 12px; margin-bottom: 0.4rem; }
textarea, .stTextInput > div > div > input { border-radius: 8px !important; font-size: 0.88rem !important; }
[data-testid="stExpander"] { border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; margin-top: 0.5rem; }
</style>
"""


# Pronunciation dictionary for common programming terms
PRONUNCIATION_DICT = {
    "def": "define",
    "for": "for loop",
    "while": "while loop",
    "if": "if condition",
    "elif": "else if",
    "else": "else condition",
    "return": "return statement",
    "->": "returns",
    "=": "equals",
    "==": "is equal to",
    "!=": "is not equal to",
    "fibonacci": "fib-oh-nah-chee",  # Example for specific terms
    # Add more terms as needed
}

def preprocess_text_for_tts(text):
    """
    Preprocess LLM response text for TTS:
      1. Strip markdown formatting (headers, bold, italic, code, bullets)
      2. Apply pronunciation dictionary
      3. Remove remaining symbols that confuse TTS
    """
    try:
        processed_text = text

        # ── Step 1: Strip markdown ─────────────────────────────────────────────
        # Remove fenced code blocks (```...```)
        processed_text = re.sub(r'```[\s\S]*?```', ' code block. ', processed_text)
        # Remove inline code (`...`)
        processed_text = re.sub(r'`[^`]+`', '', processed_text)
        # Remove ATX headers (## Heading)
        processed_text = re.sub(r'#{1,6}\s+', '', processed_text)
        # Remove bold/italic markers (**, __, *, _)
        processed_text = re.sub(r'\*{1,3}|_{1,3}', '', processed_text)
        # Remove bullet / ordered list markers at line start
        processed_text = re.sub(r'^\s*[-*+]\s+', '', processed_text, flags=re.MULTILINE)
        processed_text = re.sub(r'^\s*\d+\.\s+', '', processed_text, flags=re.MULTILINE)
        # Remove blockquote markers
        processed_text = re.sub(r'^\s*>\s+', '', processed_text, flags=re.MULTILINE)
        # Remove HTML tags
        processed_text = re.sub(r'<[^>]+>', '', processed_text)
        # Remove markdown links [text](url) → keep text only
        processed_text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', processed_text)
        # Remove standalone URLs
        processed_text = re.sub(r'https?://\S+', '', processed_text)
        # Remove horizontal rules
        processed_text = re.sub(r'^[-_*]{3,}\s*$', '', processed_text, flags=re.MULTILINE)

        # ── Step 2: Apply pronunciation dictionary ─────────────────────────────
        for term, pronunciation in PRONUNCIATION_DICT.items():
            processed_text = re.sub(r'\b' + re.escape(term) + r'\b', pronunciation, processed_text)
        
        # ── Step 3: Clean up remaining symbols ────────────────────────────────
        processed_text = re.sub(r'[\(\)\[\]\{\}]', '', processed_text)  # Remove brackets
        processed_text = re.sub(r'[=+\-*/\\|<>^~]', ' ', processed_text)  # Replace operators with spaces
        processed_text = re.sub(r'\s+', ' ', processed_text).strip()  # Normalize spaces
        
        return processed_text
    except Exception as e:
        st.error(f"Text preprocessing failed: {e}")
        return text  # Fallback to original text
    

def type_writer_effect(text, speed=0.02, enable_tts=False):
    """
    Display text in Streamlit as if it's being typed out.
    Optionally plays TTS audio after completion.
    """
    placeholder = st.empty()
    displayed_text = ""
    for char in text:
        displayed_text += char
        placeholder.markdown(displayed_text)
        time.sleep(speed)
    if enable_tts:
        # Preprocess text for TTS
        processed_text = preprocess_text_for_tts(text)
        audio_file = speak_text(processed_text)
        if audio_file:
            st.audio(audio_file, format='audio/mp3')

def speak_text(text):
    """
    Generate TTS audio from text and return BytesIO for st.audio.
    """
    try:
        # Preprocess text for better pronunciation
        processed_text = preprocess_text_for_tts(text)
        
        # Truncate text to avoid gTTS limitations
        processed_text = processed_text[:5000]
        tts = gTTS(text=processed_text, lang='en', slow=False)
        audio_file = io.BytesIO()
        tts.write_to_fp(audio_file)
        audio_file.seek(0)
        return audio_file
    except Exception as e:
        st.error(f"TTS generation failed: {e}")
        return None
def handle_tts_feedback():
    """
    Allow users to report mispronounced words and suggest corrections.
    """
    st.subheader("🔊 TTS Feedback")
    with st.form(key="tts_feedback_form"):
        mispronounced_word = st.text_input("Mispronounced Word:", placeholder="e.g., Backford")
        suggested_pronunciation = st.text_input("Suggested Pronunciation:", placeholder="e.g., backward")
        submit_feedback = st.form_submit_button("Submit Feedback")
        if submit_feedback and mispronounced_word and suggested_pronunciation:
            # Store feedback (e.g., in a file or database)
            with open("tts_feedback.txt", "a") as f:
                f.write(f"{mispronounced_word}:{suggested_pronunciation}\n")
            st.success(f"Thank you! Added '{mispronounced_word}' as '{suggested_pronunciation}' to feedback.")
# ------------------------------
# Recursion Visualization Functions
# ------------------------------

def generate_uuid():
    return str(uuid.uuid4())

def create_recursion_tree(func_name, input_val, calls, step):
    """
    Build a static Plotly graph showing the recursion tree up to `step` calls.
    The currently-added node (calls[step-1]) is highlighted in red.
    """
    if not calls or step < 1:
        return None

    step = min(step, len(calls))
    visible = calls[:step]

    # Build position/label arrays for visible nodes
    node_x, node_y, labels, hover_texts, colors, sizes = [], [], [], [], [], []
    idx_to_pos = {}   # call index → position in visible list

    for pos, (args, depth, idx, parent_idx, result, memoized) in enumerate(visible):
        idx_to_pos[idx] = pos
        node_x.append(idx)
        node_y.append(-depth)

        args_str = ", ".join(str(a) for a in args)
        label = f"{func_name}({args_str})"
        hover = f"{func_name}({args_str}) = {result}"
        if memoized:
            hover += "<br>Memoized: Yes"
        labels.append(label)
        hover_texts.append(hover)

        is_current = (pos == step - 1)
        colors.append("red" if is_current else f"hsl({depth * 60 % 360}, 70%, 50%)")
        sizes.append(35 if is_current else 25)

    # Build edges only between visible nodes
    edge_x, edge_y = [], []
    for pos, (args, depth, idx, parent_idx, result, memoized) in enumerate(visible):
        if parent_idx is not None and parent_idx in idx_to_pos:
            pp = idx_to_pos[parent_idx]
            edge_x += [node_x[pp], node_x[pos], None]
            edge_y += [node_y[pp], node_y[pos], None]

    # Annotation for the current (highlighted) node
    cur = visible[-1]
    cur_args_str = ", ".join(str(a) for a in cur[0])
    ann_text = f"Step {step}/{len(calls)}: {func_name}({cur_args_str}) = {cur[4]}"
    annotation = dict(
        x=node_x[-1], y=node_y[-1],
        xref="x", yref="y",
        text=ann_text,
        showarrow=True, arrowhead=2,
        ax=20, ay=-30,
        font=dict(size=12, color="yellow"),
        bgcolor="black", bordercolor="white", opacity=0.8
    )

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode="markers+text",
        text=labels,
        textposition="bottom center",
        hoverinfo="text",
        hovertext=hover_texts,
        marker=dict(size=sizes, color=colors,
                    line=dict(width=2, color="white"), symbol="circle"),
        textfont=dict(size=12, color="white")
    )
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        mode="lines",
        line=dict(width=2, color="rgba(200,200,200,0.6)"),
        hoverinfo="none"
    )

    all_y = [-c[1] for c in calls]   # full depth range for stable axes
    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            title=dict(
                text=f"Recursion Tree — {func_name}({input_val})  "
                     f"(Step {step}/{len(calls)})",
                font=dict(size=18, color="white"),
                x=0.5, xanchor="center"
            ),
            showlegend=False,
            plot_bgcolor="#0d0d0d",
            paper_bgcolor="#0d0d0d",
            xaxis=dict(showgrid=False, zeroline=False, visible=False,
                       range=[-0.5, len(calls) - 0.5]),
            yaxis=dict(showgrid=False, zeroline=False, visible=False,
                       range=[min(all_y) - 1, 1]),
            margin=dict(l=10, r=10, t=60, b=10),
            annotations=[annotation]
        )
    )
    return fig

def run_app():
    st.set_page_config(
        page_title="ExplainMate – Code Explainer",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    # Inject CSS immediately after set_page_config (must be first Streamlit call)
    st.markdown(_APP_CSS, unsafe_allow_html=True)
    
    # ── Sidebar ────────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("## ⚙️ Settings")
        st.divider()

        enable_tts = st.checkbox("🔊 Enable Text-to-Speech", value=False,
                                  help="Reads AI responses aloud after generation")
        if enable_tts:
            st.success("🎵 TTS active")

        st.divider()
        st.markdown("## 🌐 Language")
        languages = [
            "python", "javascript", "cpp", "java", "html", "css", "json",
            "typescript", "kotlin", "swift", "php", "ruby", "go", "r",
            "scala", "haskell", "lua", "perl", "dart", "bash", "rust",
            "sql", "yaml", "xml", "markdown"
        ]
        selected_lang = st.selectbox("Code Language", languages, index=0,
                                      label_visibility="collapsed")
        st.caption(f"✅ Active: **{selected_lang.upper()}**")

        st.divider()
        st.caption("ExplainMate v2.0 · Built with Streamlit")
        code = ""  # initialise before ace widget

    # ── Header ─────────────────────────────────────────────────────────────────
    st.markdown(
        """<h1 style='margin-bottom:0'>🚀 ExplainMate</h1>
        <p style='color:rgba(255,255,255,0.5);margin-top:4px;font-size:1rem'>
        AI-powered Code Explainer &amp; Interview Prep Assistant
        </p>""",
        unsafe_allow_html=True
    )
    st.divider()

    # ── Code Editor ────────────────────────────────────────────────────────────
    col_editor, col_stdin = st.columns([3, 1])
    with col_editor:
        st.caption("📝 Code Editor — paste or type your code below")
        code = st_ace(
            language=selected_lang, theme="terminal",
            height=280, placeholder="Paste your code here...",
            key="main_editor"
        )
    with col_stdin:
        st.caption("⌨️ Stdin (optional)")
        stdin_data = st.text_area(
            "Input Data", height=180,
            placeholder="Enter stdin if needed...",
            label_visibility="collapsed"
        )

    # Run button
    btn_run, btn_ask_col = st.columns([2, 3])
    with btn_run:
        run_clicked = st.button("▶️ Run Code", type="primary", use_container_width=True)
    with btn_ask_col:
        follow_up = st.text_input(
            "follow_up", label_visibility="collapsed",
            placeholder="❓ Quick question about the code... (press Ask)",
            max_chars=200
        )

    if run_clicked:
        if code.strip():
            with st.spinner(f"Running {selected_lang.upper()} code…"):
                output = run_code(selected_lang, code, stdin=stdin_data)
            st.success("✅ Executed successfully")
            st.code(output, language="text")
        else:
            st.warning("⚠️ Please paste code before running.")

    if follow_up:
        if st.button("💭 Ask", type="secondary"):
            if code.strip():
                with st.spinner("Thinking…"):
                    _outline, _ = prepare_outline(code, selected_lang)
                    response = query_llm(prompts.followup_prompt(code, follow_up, _outline))
                with st.expander("📝 Response", expanded=True):
                    type_writer_effect(response, enable_tts=enable_tts)
            else:
                st.warning("⚠️ Paste some code first.")

    st.divider()

    # ── Outline & tabs ─────────────────────────────────────────────────────────
    if code.strip():
        outline, complexity_hint = prepare_outline(code, selected_lang)
    else:
        outline, complexity_hint = ("", "")

    _NO_CODE_MSG = """
    <div class='empty-state'>
        📋 <strong>No code detected.</strong><br>
        Paste your code in the editor above, then click a button here.
    </div>"""

    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
        "💡 Explanation", "📊 Complexity", "🎯 Interview",
        "🧪 Edge Cases", "🐞 Bugs", "⚡ Optimize",
        "🤔 What-If", "🗣️ Assistant", "🧮 Viz Complexity", "📈 Viz Recursion"
    ])

    
    # ── Tab 1 · Explanation ────────────────────────────────────────────────────
    with tab1:
        st.subheader("💡 Detailed Code Explanation")
        if not code.strip():
            st.markdown(_NO_CODE_MSG, unsafe_allow_html=True)
        else:
            if st.button("🔍 Generate Explanation", type="primary"):
                with st.spinner("Explaining code…"):
                    response = query_llm(prompts.explanation_prompt(code, outline, complexity_hint))
                col_a, col_b = st.columns(2)
                with col_a:
                    with st.expander("📜 Code Outline", expanded=True):
                        st.code(outline, language="text")
                with col_b:
                    with st.expander("📝 Explanation", expanded=True):
                        type_writer_effect(response, enable_tts=enable_tts)

    # ── Tab 2 · Complexity ─────────────────────────────────────────────────────
    with tab2:
        st.subheader("📊 Time & Space Complexity")
        if not code.strip():
            st.markdown(_NO_CODE_MSG, unsafe_allow_html=True)
        else:
            if st.button("📈 Analyze Complexity", type="primary"):
                with st.spinner("Analyzing…"):
                    response = query_llm(prompts.complexity_prompt(code, outline, complexity_hint))
                st.info(f"🧠 Quick estimate: **{complexity_hint}**")
                with st.expander("🔍 Detailed AI Analysis", expanded=True):
                    type_writer_effect(response, enable_tts=enable_tts)

    # ── Tab 3 · Interview ──────────────────────────────────────────────────────
    with tab3:
        st.subheader("🎯 Interview Preparation")
        if not code.strip():
            st.markdown(_NO_CODE_MSG, unsafe_allow_html=True)
        else:
            st.caption("Choose a question style — each generates a fresh set of interview questions.")
            c1, c2, c3, c4 = st.columns(4)
            btn_std  = c1.button("🧠 Standard Q&A",   type="secondary", use_container_width=True)
            btn_diff = c2.button("📊 By Difficulty",   type="secondary", use_container_width=True)
            btn_wb   = c3.button("📋 Whiteboard",      type="secondary", use_container_width=True)
            btn_to   = c4.button("⚖️ Trade-Offs",      type="secondary", use_container_width=True)

            if btn_std:
                with st.spinner("Generating Standard Q&A…"):
                    response = query_llm(prompts.interview_prompt(code, outline))
                with st.expander("Questions & Answers", expanded=True):
                    type_writer_effect(response, enable_tts=enable_tts)
            if btn_diff:
                with st.spinner("Generating Difficulty-based Questions…"):
                    response = query_llm(prompts.difficulty_based_questions_prompt(code, outline))
                with st.expander("Easy / Medium / Hard", expanded=True):
                    type_writer_effect(response, enable_tts=enable_tts)
            if btn_wb:
                with st.spinner("Preparing Whiteboard Mock…"):
                    response = query_llm(prompts.whiteboard_questions_prompt(code, outline))
                with st.expander("Whiteboard Mock Session", expanded=True):
                    type_writer_effect(response, enable_tts=enable_tts)
            if btn_to:
                with st.spinner("Analyzing Trade-Offs…"):
                    response = query_llm(prompts.tradeoff_explanation_prompt(code, outline))
                with st.expander("Trade-Off Analysis", expanded=True):
                    type_writer_effect(response, enable_tts=enable_tts)
    
    # ── Tab 4 · Edge Cases ─────────────────────────────────────────────────────
    with tab4:
        st.subheader("🧪 Edge Case Testing")
        if not code.strip():
            st.markdown(_NO_CODE_MSG, unsafe_allow_html=True)
        else:
            st.caption("Generates 5 edge test cases with inputs, expected outputs, and reasons.")
            if st.button("🧪 Generate Edge Cases", type="primary"):
                with st.spinner("Finding edge cases…"):
                    response = query_llm(prompts.edge_case_prompt(code, outline))
                with st.expander("Edge Case Report", expanded=True):
                    type_writer_effect(response, enable_tts=enable_tts)

    # ── Tab 5 · Bug Finder ─────────────────────────────────────────────────────
    with tab5:
        st.subheader("🐞 Bug Detection & Fixes")
        if not code.strip():
            st.markdown(_NO_CODE_MSG, unsafe_allow_html=True)
        else:
            st.caption("Scans for bugs, bad practices, missing edge case handling, and suggests fixes.")
            if st.button("🔍 Hunt Bugs", type="primary"):
                with st.spinner("Scanning for bugs…"):
                    response = query_llm(prompts.bug_finder_prompt(code, outline))
                with st.expander("Bug Report & Fixes", expanded=True):
                    type_writer_effect(response, enable_tts=enable_tts)

    # ── Tab 6 · Optimize ──────────────────────────────────────────────────────
    with tab6:
        st.subheader("⚡ Optimization Suggestions")
        if not code.strip():
            st.markdown(_NO_CODE_MSG, unsafe_allow_html=True)
        else:
            st.caption("Suggests a faster / more memory-efficient version with trade-off comparison.")
            if st.button("🚀 Optimize Code", type="primary"):
                with st.spinner("Optimizing…"):
                    response = query_llm(prompts.optimization_prompt(code, outline))
                with st.expander("Optimized Version", expanded=True):
                    type_writer_effect(response, enable_tts=enable_tts)

    # ── Tab 7 · What-If ───────────────────────────────────────────────────────
    with tab7:
        st.subheader("🤔 What-If Scenarios")
        if not code.strip():
            st.markdown(_NO_CODE_MSG, unsafe_allow_html=True)
        else:
            st.caption("Pick a scenario to explore how your code behaves under different conditions.")
            common_questions = [
                ("📦 Very Large Input",   "What if input is very large?"),
                ("🔁 Duplicate Values",   "What if there are duplicates?"),
                ("📈 Pre-sorted Array",  "What if the array is sorted?"),
            ]
            for i, (label, q) in enumerate(common_questions):
                with st.container(border=True):
                    col_q, col_btn = st.columns([5, 1])
                    col_q.markdown(f"**{label}** — _{q}_")
                    if col_btn.button("Analyze", key=f"what_if_{i}", type="secondary"):
                        with st.spinner(f"Analyzing: {q}"):
                            response = query_llm(prompts.followup_prompt(code, q, outline))
                        with st.expander(label, expanded=True):
                            type_writer_effect(response, enable_tts=enable_tts)
    
    # ── Tab 8 · AI Assistant ───────────────────────────────────────────────────
    with tab8:
        st.subheader("🗣️ AI Assistant")

        # ─ Voice input ──────────────────────────────────────────────────
        with st.expander("🎤 Voice-to-Text (click to expand)"):
            st.caption("Speak a question about your code and get an AI response.")
            if st.button("🎤 Start Recording", type="secondary"):
                voice_input = voice_to_text()
                if voice_input:
                    st.chat_message("user").markdown(f"**Voice Input:** {voice_input}")
                    with st.spinner("Responding…"):
                        response = query_llm(prompts.followup_prompt(code, voice_input, outline))
                    st.chat_message("assistant").markdown(response)
                    if enable_tts:
                        speak_text(response)

        # ─ Chat ────────────────────────────────────────────────────────
        col_chat_hdr, col_clear = st.columns([5, 1])
        col_chat_hdr.markdown("**💬 Chat with AI**")
        if col_clear.button("Clear", type="secondary", key="clear_chat"):
            st.session_state.messages = []
            st.rerun()

        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if not code.strip():
            st.caption("⚠️ Paste code in the editor above for context-aware answers.")

        if prompt := st.chat_input("Ask about the code…"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.spinner("Thinking…"):
                with st.chat_message("assistant"):
                    response = query_llm(prompts.followup_prompt(code, prompt, outline))
                    st.markdown(response)
                    if enable_tts:
                        speak_text(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
    
    # ── Tab 9 · Viz Complexity ───────────────────────────────────────────────────
    with tab9:
        st.subheader("🧮 Complexity Visualization")
        if st.button("🔍 Visualize Complexity", type="primary"):
            with st.spinner("Generating visuals..."):
                time_c = heuristic_time_complexity(code)
                space_c = heuristic_space_complexity(code)
                
                def extract_functions_and_loops(code_text, lang):
                    patterns = {
                        "default": r'(?:def|function|void|int|float|double|public|private|protected|static)\s+(\w+)\s*\(',
                        "python": r'def\s+(\w+)\s*\(',
                        "javascript": r'(?:function\s+(\w+)|(\w+)\s*=\s*\([^)]*\)\s*=>)',
                        "java": r'(?:public|private|protected|static)?\s+\w+\s+(\w+)\s*\('
                    }
                    func_pattern = patterns.get(lang, patterns["default"])
                    funcs = [f for f in re.findall(func_pattern, code_text) if f]
                    loops = len(re.findall(r'\b(for|while|foreach|do)\b', code_text))
                    return funcs, loops
                
                funcs, loops = extract_functions_and_loops(code, selected_lang)
                
                sub_tab1, sub_tab2, sub_tab3 = st.tabs(["📊 Summary", "📈 Graphs", "🐍 Python"])
                with sub_tab1:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                        st.metric("Time Complexity", time_c)
                        st.markdown('</div>', unsafe_allow_html=True)
                    with col2:
                        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                        st.metric("Space Complexity", space_c)
                        st.markdown('</div>', unsafe_allow_html=True)
                    with col3:
                        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                        st.metric("Functions", len(set(funcs)))
                        st.markdown('</div>', unsafe_allow_html=True)
                    st.metric("Loops", loops)
                
                with sub_tab2:
                    col_graph1, col_graph2 = st.columns(2)
                    with col_graph1:
                        graph_buffer, _, _ = generate_complexity_graph(code)
                        st.image(graph_buffer, caption=f"Complexity Trade-off ({selected_lang})", use_container_width=True)
                    with col_graph2:
                        st.info("📊 Bar chart: Time vs Space comparison")
                
                with sub_tab3:
                    if selected_lang == "python":
                        report = cyclomatic_complexity_report(code)
                        st.code(report, language="text")
                        graph_buffer = generate_function_call_graph(code)
                        if graph_buffer:
                            st.image(graph_buffer, caption="Function Call Graph", use_container_width=True)
                    else:
                        st.info("🐍 Available only for Python.")
    
    # ── Tab 10 · Viz Recursion ──────────────────────────────────────────────────
    with tab10:
        st.subheader("📈 Recursion Tree Visualizer")
        st.caption("💡 Tip: paste any Python recursive function, enter the input, then step through each call.")
        if selected_lang != "python":
            st.warning("⚠️ Recursion visualization is only available for Python code.")
        else:
            default_recursive_code = """def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)"""
            # Always start with the default code, not the main editor's content
            # (Main editor code is often non-recursive which confuses the tracer)
            if "rec_code" not in st.session_state:
                st.session_state["rec_code"] = default_recursive_code

            col_load, _ = st.columns([2, 5])
            with col_load:
                if st.button("📋 Load from Editor", help="Copy code from main editor into this box"):
                    st.session_state["rec_code"] = code or default_recursive_code
                    st.rerun()

            recursion_code = st.text_area(
                "Recursive Code:",
                value=st.session_state["rec_code"],
                height=200,
                key="rec_code_area"
            )
            st.session_state["rec_code"] = recursion_code
            recursion_input = st.text_input("Input (e.g., 5 or 10):", "5")

            if st.button("🎬 Trace Calls", type="primary"):
                try:
                    input_eval = eval(recursion_input)
                    with st.spinner("Tracing recursive calls..."):
                        calls, error = execute_instrumented_code(recursion_code, input_eval)
                    if error:
                        st.error(f"❌ {error}")
                    else:
                        func_name = get_first_function_name(recursion_code)
                        if not func_name:
                            st.error("❌ No function found in the code.")
                        else:
                            st.session_state["rec_calls"] = calls
                            st.session_state["rec_func"] = func_name
                            st.session_state["rec_input"] = input_eval
                            st.session_state["rec_step"] = 1
                            st.success(f"✅ Traced {len(calls)} recursive calls!")
                except Exception as e:
                    st.error(f"❌ Invalid input: {e}")

            # Step-through controls (only shown after tracing)
            if "rec_calls" in st.session_state:
                calls     = st.session_state["rec_calls"]
                func_name = st.session_state["rec_func"]
                input_val = st.session_state["rec_input"]
                total     = len(calls)

                # Clamp stale session step to valid range
                saved_step = min(st.session_state.get("rec_step", 1), total)

                # Only show slider when there are multiple steps
                if total > 1:
                    step = st.slider(
                        "📍 Step", min_value=1, max_value=total,
                        value=saved_step,
                        key="rec_slider"
                    )
                else:
                    step = 1
                    st.info("ℹ️ Only 1 call recorded (base case or non-recursive function).")

                st.session_state["rec_step"] = step

                # Prev / Next buttons (only useful when total > 1)
                if total > 1:
                    col_prev, col_next, col_info = st.columns([1, 1, 4])
                    with col_prev:
                        if st.button("⬅️ Prev", use_container_width=True):
                            st.session_state["rec_step"] = max(1, step - 1)
                            st.rerun()
                    with col_next:
                        if st.button("➡️ Next", use_container_width=True):
                            st.session_state["rec_step"] = min(total, step + 1)
                            st.rerun()
                    with col_info:
                        cur = calls[step - 1]
                        args_str = ", ".join(str(a) for a in cur[0])
                        memo_tag = " 🔁 (memoized)" if cur[5] else ""
                        st.info(
                            f"**{func_name}({args_str})** → `{cur[4]}`{memo_tag}  "
                            f"| depth {cur[1]}"
                        )
                else:
                    cur = calls[0]
                    args_str = ", ".join(str(a) for a in cur[0])
                    st.info(f"**{func_name}({args_str})** → `{cur[4]}` | depth {cur[1]}")

                fig = create_recursion_tree(func_name, input_val, calls, step=step)
                if fig:
                    st.plotly_chart(fig, use_container_width=True, height=680)
                else:
                    st.error("❌ Tree generation failed.")
    
    # Footer
    # ── Footer ───────────────────────────────────────────────────────────────
    st.divider()
    st.markdown(
        "<p style='text-align:center;color:rgba(255,255,255,0.3);font-size:0.8rem'>"
        "👨‍💻 Built with ❤️ using Streamlit &middot; Powered by Google Gemini &middot; © 2025 ExplainMate"
        "</p>",
        unsafe_allow_html=True
    )

def prepare_outline(code_text, lang):
    if lang != "python":
        return generate_outline(code_text, lang=lang), "Heuristic applied."
    outline = generate_outline(code_text, lang="python")
    complexity_hint = guess_time_complexity(code_text)
    return outline, complexity_hint

def voice_to_text():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        with st.spinner("Listening... Speak now!"):
            try:
                audio = r.listen(source, timeout=5, phrase_time_limit=20)
                text = r.recognize_google(audio)
                return text
            except sr.WaitTimeoutError:
                st.warning("⏰ Timeout. Try again.")
            except sr.UnknownValueError:
                st.error("🤷 Could not understand.")
            except sr.RequestError as e:
                st.error(f"🌐 Error: {e}")
    return ""

if __name__ == "__main__":
    run_app()