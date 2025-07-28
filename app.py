import streamlit as st
from core.hf_llm import query_llm
from core import prompts
import speech_recognition as sr
from core.code_runner import run_code
from streamlit_ace import st_ace
from utils.utils_ast import generate_outline
from utils.utils_complexity import guess_time_complexity
from utils.utils_complexity_advanced import (
    cyclomatic_complexity_report,
    generate_function_call_graph,
)
from utils.utils_complexity_generic import heuristic_time_complexity, heuristic_space_complexity, generate_complexity_graph
import re
import time


def type_writer_effect(text, speed=0.02):
    """
    Display text in Streamlit as if it's being typed out.
    """
    placeholder = st.empty()
    displayed_text = ""
    for char in text:
        displayed_text += char
        placeholder.markdown(displayed_text)
        time.sleep(speed)

def run_app():
    # Page Config
    st.set_page_config(page_title="Advanced Code Explainer Dashboard", layout="wide")
    st.title("🚀 Advanced Code Explainer + Interview Prep Assistant")

    # Supported languages
    languages = [
        "python", "javascript", "cpp", "java", "html", "css", "json",
        "typescript", "kotlin", "swift", "php", "ruby", "go", "r",
        "scala", "haskell", "lua", "perl", "dart", "bash", "rust",
        "sql", "yaml", "xml", "markdown"
    ]
    selected_lang = st.selectbox("Select Code Language:", languages, index=0)
    st.write(f"**Selected Language:** {selected_lang}")

    # Code Editor
    code = st_ace(language=selected_lang, theme="terminal", height=300, key="code_editor")
    stdin_data = st.text_area("Enter input for your code (if any):")
    # Run code button (below code editor)
    col_left, col_right = st.columns([2, 1])
    with col_left:
        if st.button("▶️ Run Code"):
            if code.strip():
                status_box = st.empty()
                status_box.info(f"Running {selected_lang} code...")
                output = run_code(selected_lang, code, stdin=stdin_data)
                status_box.empty()            
                st.subheader("Output:")
                st.code(output, language="text")
            else:
                st.warning("Please paste code before running.")

    with col_right:
        if not code.strip():
            st.warning("Please paste code in the editor to start analysis.")

    follow_up = st.text_input("Ask a follow-up question (e.g., What if input is large?)")

    def prepare_outline(code_text):
        if selected_lang != "python":
            return generate_outline(code_text, lang=selected_lang), "Complexity estimation heuristic applied."
        outline = generate_outline(code_text, lang="python")
        complexity_hint = guess_time_complexity(code_text)
        return outline, complexity_hint

    def voice_to_text():
        r = sr.Recognizer()
        with sr.Microphone() as source:
            status_box = st.empty()
            status_box.info("🎤 Listening... Please speak now.")
            try:
                audio = r.listen(source, timeout=5, phrase_time_limit=20)
                status_box.empty()
                text = r.recognize_google(audio)
                st.success(f"Recognized Text: {text}")
                return text
            except sr.WaitTimeoutError:
                status_box.empty()
                st.warning("No voice input detected within the timeout. Please try again.")
            except sr.UnknownValueError:
                status_box.empty()
                st.error("Sorry, I could not understand your speech.")
            except sr.RequestError as e:
                status_box.empty()
                st.error(f"Could not request results; {e}")
        return ""



    if code:
        outline, complexity_hint = prepare_outline(code)
    else:
        outline, complexity_hint = ("", "")

    # Follow-up Question
    if follow_up and st.button("❓ Ask a Question"):
        response = query_llm(prompts.followup_prompt(code, follow_up, outline))
        with st.expander("Follow-up Answer"):
            type_writer_effect(response, speed=0.02)
    # Tabs with emojis
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
        "💡 Explanation", 
        "📊 Complexity", 
        "🎯 Interview Questions", 
        "🧪 Edge Cases",
        "🐞 Bug Finder",
        "⚡ Code Optimization",
        "🤔 What-If Analyzer",
        "🗣️ AI Assistant",
        "🧮 Complexity Visualization"
    ])

    # Tab 1 - Explanation
    with tab1:
        st.markdown("### 💡 Code Explanation")
        if st.button("🔍 Explain Code"):
            response = query_llm(prompts.explanation_prompt(code, outline, complexity_hint))
            st.success("Code explanation generated successfully!")
            with st.expander("📜 **Code Outline**"):
                st.code(outline, language="text")
            with st.expander("📝 **LLM Explanation**"):
                type_writer_effect(response, speed=0.02)


    # Tab 2 - Complexity
    with tab2:
        st.markdown("### 📊 Time & Space Complexity Analysis")
        if st.button("📊 Analyze Complexity"):
            response = query_llm(prompts.complexity_prompt(code, outline, complexity_hint))
            st.info(f"**Initial Guess:** {complexity_hint}")
            with st.expander("🔍 **Detailed LLM Complexity Analysis**"):
                type_writer_effect(response, speed=0.02)


    # Tab 3 - Interview Questions
    with tab3:
        st.markdown("### 🎯 Interview Prep Add-Ons")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🧠 Standard Interview Questions"):
                response = query_llm(prompts.interview_prompt(code, outline))
                with st.expander("Questions & Answers"):
                    type_writer_effect(response, speed=0.02)

            if st.button("📊 Questions by Difficulty"):
                response = query_llm(prompts.difficulty_based_questions_prompt(code, outline))
                with st.expander("Easy/Medium/Hard Questions"):
                    type_writer_effect(response, speed=0.02)

        with col2:
            if st.button("📋 Mock Whiteboard Questions"):
                response = query_llm(prompts.whiteboard_questions_prompt(code, outline))
                with st.expander("Mock Whiteboard Q&A"):
                    type_writer_effect(response, speed=0.02)

            if st.button("⚖️ Trade-Offs Explanation"):
                response = query_llm(prompts.tradeoff_explanation_prompt(code, outline))
                with st.expander("Trade-Offs Analysis"):
                    type_writer_effect(response, speed=0.02)

    # Tab 4 - Edge Cases
    with tab4:
        st.markdown("### 🧪 Edge Case Tester")
        if st.button("Generate Edge Cases"):
            response = query_llm(prompts.edge_case_prompt(code, outline))
            with st.expander("Edge Cases with Expected Outputs"):
                type_writer_effect(response, speed=0.02)


    # Tab 5 - Bug Finder
    with tab5:
        st.markdown("### 🐞 Bug Finder & Fixer")
        if st.button("Find Bugs & Fixes"):
            response = query_llm(prompts.bug_finder_prompt(code, outline))
            with st.expander("Bug Report & Fix Suggestions"):
                type_writer_effect(response, speed=0.02)

    # Tab 6 - Code Optimization
    with tab6:
        st.markdown("### ⚡ Code Optimization Suggestions")
        if st.button("Suggest Optimizations"):
            response = query_llm(prompts.optimization_prompt(code, outline))
            with st.expander("Optimized Code & Analysis"):
                type_writer_effect(response, speed=0.02)


    # Tab 7 - What-If Analyzer
    with tab7:
        st.markdown("### 🤔 What-If Analyzer")
        common_questions = [
            "What if input is very large?",
            "What if there are duplicates?",
            "What if the array is sorted?"
        ]
        for q in common_questions:
            if st.button(q):
                response = query_llm(prompts.followup_prompt(code, q, outline))
                with st.expander(f"Answer for: {q}"):
                    type_writer_effect(response, speed=0.02)

    # Tab 8 - AI Assistant
    with tab8:
        st.markdown("### 🗣️ Voice & AI Assistant")
        st.write("#### 🎤 Voice-to-Text Input")
        if st.button("🎙 Record Voice"):
            voice_input = voice_to_text()
            if voice_input:
                st.write(f"**Your Question:** {voice_input}")
                response = query_llm(prompts.followup_prompt(code, voice_input, outline))
                type_writer_effect(response, speed=0.02)


        st.write("#### 💬 AI Chat Mode")
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        user_input = st.text_input("Ask anything about the code:")
        if st.button("Send Question"):
            if user_input:
                response = query_llm(prompts.followup_prompt(code, user_input, outline))
                st.session_state.chat_history.append(("User", user_input))
                st.session_state.chat_history.append(("Assistant", response))
        for role, msg in st.session_state.chat_history:
            if role == "User":
                st.markdown(f"**👤 You:** {msg}")
            else:
                st.markdown(f"**🤖 Assistant:** {msg}")

    # Tab 9 - Complexity Visualization
    with tab9:
        st.markdown("### 🧮 Complexity Visualization")

        if st.button("🔍 Analyze Code Complexity"):
            # Heuristic complexity report
            time_c = heuristic_time_complexity(code)
            space_c = heuristic_space_complexity(code)

            # Extract functions & loops (generic)
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

            # --- Use tabs for better UX ---
            sub_tab1, sub_tab2, sub_tab3 = st.tabs(["📑 Summary", "📊 Graphs", "🐍 Python-Specific"])

            with sub_tab1:
                st.subheader("Heuristic Complexity Report")
                st.write(f"**Estimated Time Complexity:** {time_c}")
                st.write(f"**Estimated Space Complexity:** {space_c}")

                st.subheader("Function & Loop Summary")
                st.write(f"**Detected Functions:** {', '.join(set(funcs)) or 'None'}")
                st.write(f"**Number of Loops:** {loops}")

            with sub_tab2:
                st.subheader("Complexity Graphs")
                col_graph1, col_graph2 = st.columns(2)
                with col_graph1:
                    graph_buffer, _, _ = generate_complexity_graph(code)
                    st.image(graph_buffer, caption=f"Time vs Space Complexity ({selected_lang})", use_container_width=True)
                with col_graph2:
                    st.info("This bar chart compares estimated time and space complexities.")

            with sub_tab3:
                if selected_lang == "python":
                    st.subheader("Cyclomatic Complexity")
                    report = cyclomatic_complexity_report(code)
                    st.code(report, language="text")

                    graph_buffer = generate_function_call_graph(code)
                    if graph_buffer:
                        # Slider to control image width
                        st.image(graph_buffer, caption="Function Call Graph", use_container_width=True)

                    else:
                        st.warning("No function call graph generated.")
                else:
                    st.info("Python-specific analysis is not available for this language.")

