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

# Custom CSS for enhanced styling
st.markdown("""
    <style>
    .main .block-container {
        padding-top: 2rem;
        padding-right: 2rem;
        padding-left: 2rem;
        padding-bottom: 1rem;
    }
    .stButton > button {
        background-color: #1f77b4;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #0d5a8a;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 0.75rem 1.5rem;
        border-radius: 8px 8px 0 0;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        border-left: 5px solid #1f77b4;
    }
    </style>
""", unsafe_allow_html=True)

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
        st.write("DEBUG: Attempting to generate TTS audio...")
        audio_file = speak_text(text)
        if audio_file:
            st.audio(audio_file, format='audio/mp3')

def speak_text(text):
    """
    Generate TTS audio from text and return BytesIO for st.audio.
    """
    try:
        st.write(f"DEBUG: Generating TTS for text (length: {len(text)} chars)")
        # Truncate text to avoid gTTS limitations
        text = text[:5000]
        tts = gTTS(text=text, lang='en', slow=False)
        audio_file = io.BytesIO()
        tts.write_to_fp(audio_file)
        audio_file.seek(0)
        # Save to a temporary file for debugging
        with open("test_tts.mp3", "wb") as f:
            f.write(audio_file.read())
        audio_file.seek(0)  # Reset buffer position
        st.write("DEBUG: Audio generated, playing in Streamlit...")
        return audio_file
    except Exception as e:
        st.error(f"TTS generation failed: {e}")
        return None

# ------------------------------
# Recursion Visualization Functions
# ------------------------------

def generate_uuid():
    return str(uuid.uuid4())

def create_recursion_tree(func_name, input_val, calls):
    if not calls:
        return None

    # Precompute positions, labels, etc.
    node_x = []
    node_y = []
    labels = []
    hover_texts = []
    colors = []

    for args, depth, idx, parent_idx, result, memoized in calls:
        x_pos = idx  # since idx sequential
        y_pos = -depth
        node_x.append(x_pos)
        node_y.append(y_pos)

        args_str = ", ".join(str(a) for a in args)
        label = f"{func_name}({args_str})"
        hover = f"{func_name}({args_str}) = {result}"
        if memoized:
            hover += "<br>Memoized: Yes"
        labels.append(label)
        hover_texts.append(hover)

        # Color based on depth
        colors.append(f"hsl({depth * 60 % 360}, 70%, 50%)")

    # Precompute full edges
    edge_x = []
    edge_y = []
    for i, (args, depth, idx, parent_idx, result, memoized) in enumerate(calls):
        if parent_idx is not None:
            parent_x = calls[parent_idx][2]  # idx of parent
            parent_y = -calls[parent_idx][1]
            x_pos = idx
            y_pos = -depth
            edge_x += [parent_x, x_pos, None]
            edge_y += [parent_y, y_pos, None]

    # Frames for animation
    frames = []
    for i in range(len(calls)):
        # Nodes up to i
        frame_node_x = node_x[:i+1]
        frame_node_y = node_y[:i+1]
        frame_labels = labels[:i+1]
        frame_hover = hover_texts[:i+1]

        # Colors and sizes, highlight i
        frame_colors = [colors[j] if j != i else "red" for j in range(i+1)]
        frame_sizes = [25 if j != i else 35 for j in range(i+1)]

        # Edges up to i
        num_edges = sum(1 for j in range(i+1) if calls[j][3] is not None)
        frame_edge_x = edge_x[:num_edges * 3]
        frame_edge_y = edge_y[:num_edges * 3]

        # Node trace
        frame_node = go.Scatter(
            x=frame_node_x, y=frame_node_y,
            mode="markers+text",
            text=frame_labels,
            textposition="bottom center",
            hoverinfo="text",
            hovertext=frame_hover,
            marker=dict(
                size=frame_sizes,
                color=frame_colors,
                line=dict(width=2, color="white"),
                symbol="circle"
            ),
            textfont=dict(size=14, color="white")
        )

        # Edge trace
        frame_edge = go.Scatter(
            x=frame_edge_x, y=frame_edge_y,
            mode="lines",
            line=dict(width=2, color="white"),
            hoverinfo="none"
        )

        # Annotation for current step
        current_args_str = ", ".join(str(a) for a in calls[i][0])
        current_result = calls[i][4]
        ann_text = f"Step {i+1}: {func_name}({current_args_str}) = {current_result}"
        frame_annotation = dict(
            x=node_x[i], y=node_y[i],
            xref="x", yref="y",
            text=ann_text,
            showarrow=True,
            arrowhead=2,
            ax=20, ay=-30,
            font=dict(size=12, color="yellow"),
            bgcolor="black",
            bordercolor="white",
            opacity=0.8
        )

        frame = go.Frame(
            data=[frame_edge, frame_node],
            layout=dict(
                annotations=[frame_annotation],
                title=dict(
                    text=f"Recursion Tree for {func_name}({input_val}) (Step {i+1}/{len(calls)})",
                    font=dict(size=20, color="white"),
                    x=0.5, xanchor="center"
                )
            )
        )
        frames.append(frame)

    # Initial frame: first node
    initial_node_x = [node_x[0]]
    initial_node_y = [node_y[0]]
    initial_labels = [labels[0]]
    initial_hover = [hover_texts[0]]
    initial_colors = ["red"]
    initial_sizes = [35]

    initial_node = go.Scatter(
        x=initial_node_x, y=initial_node_y,
        mode="markers+text",
        text=initial_labels,
        textposition="bottom center",
        hoverinfo="text",
        hovertext=initial_hover,
        marker=dict(
            size=initial_sizes,
            color=initial_colors,
            line=dict(width=2, color="white"),
            symbol="circle"
        ),
        textfont=dict(size=14, color="white")
    )

    initial_edge = go.Scatter(x=[], y=[], mode="lines", line=dict(width=2, color="white"), hoverinfo="none")

    # Figure
    fig = go.Figure(
        data=[initial_edge, initial_node],
        layout=go.Layout(
            title=dict(
                text=f"Recursion Tree for {func_name}({input_val}) (Step 1/{len(calls)})",
                font=dict(size=20, color="white"),
                x=0.5, xanchor="center"
            ),
            showlegend=False,
            plot_bgcolor="black",
            paper_bgcolor="black",
            xaxis=dict(showgrid=False, zeroline=False, visible=False, range=[-0.5, len(calls) - 0.5]),
            yaxis=dict(showgrid=False, zeroline=False, visible=False, range=[min(node_y) - 1, 1]),
            margin=dict(l=20, r=20, t=80, b=20),
            updatemenus=[
                dict(
                    type="buttons",
                    buttons=[
                        dict(label="Play", method="animate",
                             args=[None, dict(frame=dict(duration=500, redraw=True),
                                              transition=dict(duration=300),
                                              fromcurrent=True, mode="immediate")]),
                        dict(label="Pause", method="animate",
                             args=[[None], dict(frame=dict(duration=0, redraw=False),
                                                mode="immediate",
                                                transition=dict(duration=0))]),
                        dict(label="Next", method="animate",
                             args=[[None], dict(frame=dict(duration=0, redraw=True),
                                                fromcurrent=True, mode="next")]),
                        dict(label="Previous", method="animate",
                             args=[[None], dict(frame=dict(duration=0, redraw=True),
                                                fromcurrent=True, mode="previous")])
                    ],
                    direction="left",
                    pad=dict(r=10, t=87),
                    showactive=True,
                    x=0.1,
                    xanchor="right",
                    y=0,
                    yanchor="top"
                )
            ],
            annotations=[
                dict(
                    text="Use ←→ keys to navigate frames",
                    xref="paper", yref="paper",
                    x=0.005, y=-0.002,
                    showarrow=False,
                    xanchor="left", yanchor="bottom",
                    font=dict(color="white", size=12)
                )
            ]
        ),
        frames=frames
    )

    return fig

def run_app():
    st.set_page_config(page_title="Advanced Code Explainer Dashboard", layout="wide", initial_sidebar_state="expanded")
    
    # Sidebar for global settings
    with st.sidebar:
        st.header("⚙️ Settings")
        enable_tts = st.checkbox("🔊 Enable Text-to-Speech", value=False)
        if enable_tts:
            st.info("🎵 TTS enabled for responses")
        
        st.header("🌐 Languages")
        languages = [
            "python", "javascript", "cpp", "java", "html", "css", "json",
            "typescript", "kotlin", "swift", "php", "ruby", "go", "r",
            "scala", "haskell", "lua", "perl", "dart", "bash", "rust",
            "sql", "yaml", "xml", "markdown"
        ]
        selected_lang = st.selectbox("Select Code Language:", languages, index=0)
        st.info(f"Selected: **{selected_lang.upper()}**")
        
        st.header("📊 Quick Metrics")
        code = ""  # Initialize code to avoid undefined variable issues
        if 'code' in locals() and code.strip():
            with st.spinner('Analyzing...'):
                outline, _ = prepare_outline(code, selected_lang)
                if outline:
                    lines = len(code.split('\n'))
                    st.metric("Lines of Code", lines)
                    st.metric("Functions", len(re.findall(r'def\s+\w+', code)) if selected_lang == 'python' else 'N/A')

    # Main header
    st.title("🚀 ExplainMate - Advanced Code Explainer")
    st.markdown("---")
    
    # Code Editor Section
    col1, col2 = st.columns([3, 1])
    with col1:
        code = st_ace(language=selected_lang, theme="terminal", height=300, placeholder="Paste your code here...")
    with col2:
        stdin_data = st.text_area("Input Data:", height=150, placeholder="Enter stdin if needed...")
    
    # Run Code Section
    if st.button("▶️ Run & Analyze Code", type="primary", use_container_width=True):
        if code.strip():
            with st.spinner(f"Running {selected_lang} code..."):
                output = run_code(selected_lang, code, stdin=stdin_data)
            st.success("✅ Code executed successfully!")
            st.subheader("📤 Output:")
            st.code(output, language="text")
        else:
            st.warning("⚠️ Please paste code before running.")
    
    follow_up = st.text_input("❓ Follow-up Question:", placeholder="e.g., What if input is large?", max_chars=200)
    
    if follow_up and st.button("💭 Ask", type="secondary"):
        if code.strip():
            with st.spinner("Generating response..."):
                outline, _ = prepare_outline(code, selected_lang)
                response = query_llm(prompts.followup_prompt(code, follow_up, outline))
            with st.expander("📝 Response", expanded=True):
                type_writer_effect(response, enable_tts=enable_tts)
        else:
            st.warning("⚠️ Please provide code first.")

    if code.strip():
        outline, complexity_hint = prepare_outline(code, selected_lang)
    else:
        outline, complexity_hint = ("", "")

    # Enhanced Tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
        "💡 Explanation", 
        "📊 Complexity", 
        "🎯 Interview", 
        "🧪 Edge Cases",
        "🐞 Bugs",
        "⚡ Optimize",
        "🤔 What-If",
        "🗣️ Assistant",
        "🧮 Viz Complexity",
        "📈 Viz Recursion"
    ])
    
    # Tab 1 - Explanation
    with tab1:
        st.header("💡 Detailed Code Explanation")
        if st.button("🔍 Generate Explanation", type="primary"):
            with st.spinner("Explaining code..."):
                response = query_llm(prompts.explanation_prompt(code, outline, complexity_hint))
            col_a, col_b = st.columns(2)
            with col_a:
                with st.expander("📜 Code Outline"):
                    st.code(outline, language="text")
            with col_b:
                with st.expander("📝 Explanation"):
                    type_writer_effect(response, enable_tts=enable_tts)

    # Tab 2 - Complexity
    with tab2:
        st.header("📊 Time & Space Complexity")
        if st.button("📈 Analyze Complexity", type="primary"):
            with st.spinner("Analyzing..."):
                response = query_llm(prompts.complexity_prompt(code, outline, complexity_hint))
            st.info(f"🧠 Quick Guess: **{complexity_hint}**")
            with st.expander("🔍 Detailed Analysis"):
                type_writer_effect(response, enable_tts=enable_tts)

    # Tab 3 - Interview Questions
    with tab3:
        st.header("🎯 Interview Preparation")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🧠 Standard Q&A", type="secondary"):
                with st.spinner("Generating..."):
                    response = query_llm(prompts.interview_prompt(code, outline))
                with st.expander("Questions & Answers"):
                    type_writer_effect(response, enable_tts=enable_tts)
            if st.button("📊 By Difficulty", type="secondary"):
                with st.spinner("Generating..."):
                    response = query_llm(prompts.difficulty_based_questions_prompt(code, outline))
                with st.expander("Easy/Medium/Hard"):
                    type_writer_effect(response, enable_tts=enable_tts)
        with col2:
            if st.button("📋 Whiteboard Mock", type="secondary"):
                with st.spinner("Generating..."):
                    response = query_llm(prompts.whiteboard_questions_prompt(code, outline))
                with st.expander("Mock Session"):
                    type_writer_effect(response, enable_tts=enable_tts)
            if st.button("⚖️ Trade-Offs", type="secondary"):
                with st.spinner("Generating..."):
                    response = query_llm(prompts.tradeoff_explanation_prompt(code, outline))
                with st.expander("Trade-Off Analysis"):
                    type_writer_effect(response, enable_tts=enable_tts)
    
    # Tab 4 - Edge Cases
    with tab4:
        st.header("🧪 Edge Case Testing")
        if st.button("🧪 Generate Cases", type="primary"):
            with st.spinner("Testing edges..."):
                response = query_llm(prompts.edge_case_prompt(code, outline))
            with st.expander("Expected Outputs"):
                type_writer_effect(response, enable_tts=enable_tts)

    # Tab 5 - Bug Finder
    with tab5:
        st.header("🐞 Bug Detection & Fixes")
        if st.button("🔍 Hunt Bugs", type="primary"):
            with st.spinner("Scanning for bugs..."):
                response = query_llm(prompts.bug_finder_prompt(code, outline))
            with st.expander("Report & Fixes"):
                type_writer_effect(response, enable_tts=enable_tts)
    
    # Tab 6 - Code Optimization
    with tab6:
        st.header("⚡ Optimization Suggestions")
        if st.button("🚀 Optimize Code", type="primary"):
            with st.spinner("Optimizing..."):
                response = query_llm(prompts.optimization_prompt(code, outline))
            with st.expander("Improved Code"):
                type_writer_effect(response, enable_tts=enable_tts)

    # Tab 7 - What-If Analyzer
    with tab7:
        st.header("🤔 What-If Scenarios")
        common_questions = [
            "What if input is very large?",
            "What if there are duplicates?",
            "What if the array is sorted?"
        ]
        for i, q in enumerate(common_questions):
            col_q, col_btn = st.columns([3, 1])
            with col_q:
                st.write(q)
            with col_btn:
                if st.button("Analyze", key=f"what_if_{i}", type="secondary"):
                    with st.spinner("Analyzing scenario..."):
                        response = query_llm(prompts.followup_prompt(code, q, outline))
                    with st.expander(f"Response for: {q}"):
                        type_writer_effect(response, enable_tts=enable_tts)
    
    # Tab 8 - AI Assistant (Enhanced with chat_message)
    with tab8:
        st.header("🗣️ AI Assistant")
        
        # Voice Input
        st.subheader("🎤 Voice-to-Text")
        if st.button("🎙️ Start Recording", type="secondary"):
            voice_input = voice_to_text()
            if voice_input:
                st.chat_message("user").markdown(f"**Voice Input:** {voice_input}")
                with st.spinner("Responding..."):
                    response = query_llm(prompts.followup_prompt(code, voice_input, outline))
                st.chat_message("assistant").markdown(response)
                if enable_tts:
                    speak_text(response)
        
        # Chat Mode
        st.subheader("💬 Chat with AI")
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        if prompt := st.chat_input("Ask about the code..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            with st.spinner("Thinking..."):
                with st.chat_message("assistant"):
                    response = query_llm(prompts.followup_prompt(code, prompt, outline))
                    st.markdown(response)
                    if enable_tts:
                        speak_text(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Tab 9 - Complexity Visualization
    with tab9:
        st.header("🧮 Complexity Visualization")
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
    
    # Tab 10 - Recursion Visualization
    with tab10:
        st.header("📈 Recursion Tree Visualizer")
        st.info("🎬 Animate recursive calls for Python functions")
        if selected_lang != "python":
            st.error("❌ Python only for recursion viz.")
            st.stop()
        
        default_recursive_code = """def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)"""
        recursion_code = st.text_area("Recursive Code:", value=code or default_recursive_code, height=200)
        recursion_input = st.text_input("Input (e.g., 5 or [48, 18]):", "5")
        
        if st.button("🎬 Generate Tree", type="primary"):
            try:
                input_eval = eval(recursion_input)
                with st.spinner("Tracing calls..."):
                    calls, error = execute_instrumented_code(recursion_code, input_eval)
                if error:
                    st.error(error)
                else:
                    func_name = get_first_function_name(recursion_code)
                    if not func_name:
                        st.error("❌ No function found.")
                    else:
                        fig = create_recursion_tree(func_name, input_eval, calls)
                        if fig:
                            fig.update_layout(autosize=True, height=700)
                            st.plotly_chart(fig, use_container_width=True)
                            st.markdown("""
                                <script>
                                document.addEventListener('keydown', function(event) {
                                    var plot = document.getElementsByClassName('plotly')[0];
                                    if (plot) {
                                        if (event.key === 'ArrowRight') {
                                            Plotly.animate(plot, null, {frame: {duration: 0, redraw: true}, mode: 'next', fromcurrent: true});
                                        } else if (event.key === 'ArrowLeft') {
                                            Plotly.animate(plot, null, {frame: {duration: 0, redraw: true}, mode: 'previous', fromcurrent: true});
                                        }
                                    }
                                });
                                </script>
                            """, unsafe_allow_html=True)
                        else:
                            st.error("❌ Tree generation failed.")
            except Exception as e:
                st.error(f"❌ Invalid input: {e}")
    
    # Footer
    st.markdown("---")
    st.markdown("👨‍💻 Built with ❤️ using Streamlit | © 2025 ExplainMate")

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