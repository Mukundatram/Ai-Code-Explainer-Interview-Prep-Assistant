# 🚀 Advanced Code Explainer + Interview Prep Assistant

An **AI-powered Streamlit application** designed to analyze source code, explain it, evaluate complexity, generate interview questions, and even run code snippets in multiple programming languages. It is the perfect companion for developers, interview preparation, and learning.

---

## **🌟 Features**

### **1. Multi-Language Code Editor**
- Integrated **`streamlit-ace`** editor with syntax highlighting.
- Supports languages:  
  **Python, JavaScript, Java, C++, HTML, CSS, JSON, TypeScript, Go, PHP, Ruby, R, Rust, Kotlin, Swift, and more.**

---

### **2. AI-Powered Code Analysis**
- **Code Explanation**: Generates detailed explanations for each part of the code.
- **Outline Generation**: Provides a summary of functions, variables, and loops.
- **Bug Finder & Fixer**: Detects bad practices and suggests corrections.
- **Code Optimization**: Suggests performance improvements.

---

### **3. Complexity Analysis**
- **Time & Space Complexity** (heuristic-based for all languages).
- **Cyclomatic Complexity (Python Only)** using `radon`.
- **Function Call Graphs (Python Only)** using `networkx`.
- **Time vs. Space Complexity Graph** for visualization.

---

### **4. Interview Preparation**
- Auto-generates **mock interview questions** (easy, medium, hard).
- **Whiteboard Q&A** for design-based interviews.
- Explains **trade-offs between solutions**.

---

### **5. AI Assistant** 
- **Voice-to-Text Queries** using `speech_recognition`.
- **AI Chat Mode** for interactive Q&A about the code.

---

### **6. Code Execution**
- Run code in **multiple languages** using **Piston API**.
- Supports **custom stdin inputs**.
- Displays **stdout** and **stderr** outputs.

---

### **7. Visualization**
- **Interactive Tabs** for different features.
- **Complexity Graphs** (bar charts).
- **Function & Loop Summaries**.

---

## **🧠 Workflow of the Project**

# Code Explainer + Interview Prep Assistant - Detailed Workflow
<img width="657" height="960" alt="image" src="https://github.com/user-attachments/assets/ee9e1fdd-2b35-4250-8588-cdfa6f1fcca1" />


## 🗂️ Project Structure

```bash
advanced-code-explainer/
├── core/
│   ├── hf_llm.py               # LLM querying logic
│   ├── code_runner.py          # Runtime execution using Piston API
│   └── prompts.py              # Prompt templates for LLM
│
├── utils/
│   ├── __init__.py
│   ├── utils_ast.py            # AST-based outline generator
│   ├── utils_complexity.py     # Heuristic complexity guess
│   ├── utils_complexity_advanced.py  # Python cyclomatic complexity
│   └── utils_complexity_generic.py   # General language heuristics
│
├── main.py                     # Lightweight entry point for running app
├── app.py                      # Main Streamlit interface
├── requirements.txt
└── README.md



##🚀 Getting Started
1. Clone the Repository
bash
Copy
Edit
git clone https://github.com/your-username/advanced-code-explainer.git
cd advanced-code-explainer
2. Install Dependencies
Create a virtual environment (optional but recommended):

bash
Copy
Edit
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
Then install requirements:

bash
Copy
Edit
pip install -r requirements.txt
3. Run the App
bash
Copy
Edit
streamlit run main.py



