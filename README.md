# 🚀 ExplainMate - AI Code Explainer & Interview Prep Assistant

ExplainMate is an advanced, AI-powered Streamlit web application designed to help developers understand code snippet execution, analyze time and space complexity, simulate technical interviews, catch bugs, suggest optimizations, and visually trace recursive functions step-by-step.

It acts as a comprehensive "Pair Programmer" and a mentor for technical interviews, relying on **Google Gemini 2.5 Flash** for blazing-fast code analysis.

![ExplainMate Preview](https://img.shields.io/badge/Streamlit-App-FF4B4B) ![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue) ![Gemini 2.5](https://img.shields.io/badge/LLM-Gemini_2.5_Flash-orange)

## ✨ Core Features

The dashboard provides a complete suite of tools separated into interactive tabs:

- **💡 Detailed Code Explanation:** Feed in a snippet of code in any language, and the AI will scan it and break down exactly what the code is doing line-by-line using natural language and code block outlines.
- **▶️ Live Code Execution:** Run your python code instantly using the embedded local run engine, or evaluate cross-language code utilizing the JDoodle API system!
- **📊 Complexity Analysis:** Get heuristic estimations of Time & Space complexity ($O(N)$, $O(1)$) with comprehensive AI breakdowns explaining exactly *why* your functions are rated as such. Supports visualizations such as bar charts and call graphs.
- **🎯 Interview Preparation:** Get instant mock technical interviews based on your specific code!
  - Generate standard Q&A
  - Break down questions by difficulty (Easy/Medium/Hard)
  - Generate Whiteboard Mock questions
  - Evaluate coding Trade-Offs
- **🧪 Edge Case Testing:** Let the AI auto-generate 5 extreme edge cases (e.g. `null` input, massive arrays, negatives) your code might fail on and exactly what is expected to occur.
- **🐞 Bug Finder:** Scans code for anti-patterns, logical errors, and unhandled edge scenarios, providing you with a list of direct fixes.
- **⚡ Optimize Code:** Produces a rewritten, faster, and more memory-efficient version of your code alongside a trade-off comparison.
- **🤔 What-If Analyzer:** Evaluate how your code might change or fail if conditions abruptly shifted (e.g. "What if the array is pre-sorted?", "What if there are duplicates?").
- **🗣️ AI Voice Assistant:** A natural chat interface (with Voice-to-Text input AND Text-To-Speech output overrides) where you can drill down and ask specific follow-up questions contextually bound to your provided code.
- **📈 Recursion Tree Visualizer:** For Python developers, trace complex recursive algorithms (like Fibonacci or DFS) step-by-step on a beautifully rendered interactive graph. You can navigate visually using a slider or simple Next/Prev buttons!

---

## 🛠️ Installation & Setup Guide

This guide will walk you through how to set up the project on your local machine.

### Prerequisites

Ensure you have the following installed before getting started:
- Python 3.9 or higher
- A Google API Key (for Gemini 2.5 Flash LLM)
- *(Optional)* JDoodle API keys (only required if you wish to actively run non-Python languages in the code executor)

### 1. Clone & Prepare Environment

Open your terminal and create a new virtual environment to avoid conflicting packages:

```bash
git clone https://github.com/your-username/Ai-Code-Explainer-Interview-Prep-Assistant.git
cd Ai-Code-Explainer-Interview-Prep-Assistant

# Create virtual environment (Windows)
python -m venv venv
.\venv\Scripts\activate

# Create virtual environment (Mac/Linux)
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

Install all necessary libraries (Streamlit, LangChain, Google AI SDKs, Plotly, etc.):

```bash
pip install -r requirements.txt
```

### 3. Setup Environment Variables

Create a file named `.env` in the root folder of the project. You must fetch an API key from Google AI Studio. 

Populate the file exactly like this:

```env
# Required for AI explanations
GOOGLE_API_KEY=your_gemini_api_key_here

# (Optional) Required for LangSmith tracing
LANGCHAIN_TRACING_V2=true
LANGSMITH_PROJECT=your_project_name
LANGSMITH_API_KEY=your_langsmith_key

# (Optional) Required for running Non-Python code (JDoodle)
JDOODLE_CLIENT_ID=your_jdoodle_client_id_here
JDOODLE_CLIENT_SECRET=your_jdoodle_client_secret_here
```

### 4. Run the Application

Now simply boot up the Streamlit application:

```bash
streamlit run app.py
```
A browser tab will automatically open at `http://localhost:8501`.

---

## 🖱️ How to Use ExplainMate

1. **Select Language & Setup:** Use the left sidebar to select the programming language of the snippet you intend to write. You can also toggle `Text-to-Speech` if you want the AI to read the answers back to you loudly!
2. **Enter Code:** Find the main terminal editor titled `Code Editor`. Paste your snippet in here.
3. **Execute (Optional):** If you wish to run the code, drop input arguments in the `Stdin` box and click the **Run Code** button. 
4. **Interact with Tabs:** Once code is active in the editor, utilize any of the 10 tabs (`Explanation`, `Complexity`, `Interview`, `Optimize`, etc.) located below the editor to unleash AI abilities on your snippet!
5. **Trace Recursion:** Want to see the recursion tree visualizer? 
   - Ensure the language is set to `Python`
   - Paste a recursive function in the editor
   - Click the `Viz Recursion` tab
   - Click `Load from Editor`, enter an input variable, and click `Trace Calls`!

---

## 📁 Project Structure

```text
Ai-Code-Explainer-Interview-Prep-Assistant/
├── app.py                      # Main Streamlit unified UI runner
├── requirements.txt            # Python strict dependencies
├── .env                        # Private API configuration (Git ignored)
├── core/
│   ├── __init__.py
│   ├── code_runner.py          # Dual code executor (Subprocess + JDoodle)
│   ├── hf_llm.py               # LangChain integration & initialization for Gemini
│   └── prompts.py              # System prompt templates handling the 10 different tab modes
└── utils/
    ├── utils_ast.py            # AST parsers and settrace utilities for recursion visualization
    ├── utils_complexity.py     # Heuristic scanners (Loops, variables)
    ├── utils_complexity_advanced.py # Cyclomatic complexity & network graphs
    └── utils_complexity_generic.py  # Regex fallback matchers backing up the complexity tabs
```

## 🤝 Contribution

Contributions, issues, UI/UX tweaks, and feature requests are incredibly welcome! Feel free to check the issues page or submit a Pull Request.

---
*Built with ❤️, Python, Streamlit, and Google Gemini.*
