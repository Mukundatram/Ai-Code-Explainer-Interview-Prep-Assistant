def explanation_prompt(code, outline, complexity_hint):
    return (
        f"Code Outline:\\n{outline}\\n\\n"
        f"Complexity Hint: {complexity_hint}\\n\\n"
        f"Explain the following code in simple terms (max 5 lines):\\n{code}"
    )

def complexity_prompt(code, outline, complexity_hint):
    return (
        f"Code Outline:\\n{outline}\\n\\n"
        f"Initial Guess: {complexity_hint}\\n\\n"
        f"Analyze the exact time and space complexity of this code and explain briefly:\\n{code}"
    )

def followup_prompt(code, question, outline):
    return (
        f"Code Outline:\\n{outline}\\n\\n"
        f"Given this code:\\n{code}\\n\\nAnswer this question (max 3 lines): {question}"
    )

def interview_prompt(code, outline):
    return (
        f"Code Outline:\\n{outline}\\n\\n"
        f"Generate 5 concise interview questions (1 line each) based on this code:\\n{code}\\n"
        f"Provide short answers (2 lines each)."
    )

def edge_case_prompt(code, outline):
    return (
        f"Code Outline:\\n{outline}\\n\\n"
        f"List 5 edge test cases for this code with Input, Expected Output (or error), and 1-line Reason.\\n"
        f"Code:\\n{code}"
    )

def bug_finder_prompt(code, outline):
    return (
        f"Code Outline:\\n{outline}\\n\\n"
        f"Identify potential bugs, bad practices, or missed edge cases in this code and suggest fixes:\\n{code}"
    )

def optimization_prompt(code, outline):
    return (
        f"Code Outline:\\n{outline}\\n\\n"
        f"Suggest an optimized version of this code. Compare time/space trade-offs and explain improvements:\\n{code}"
    )

def whiteboard_questions_prompt(code, outline):
    return (
        f"Code Outline:\n{outline}\n\n"
        f"Convert the logic of this code into 3 mock whiteboard interview questions.\n"
        f"Include design or optimization challenges and provide short answers (max 3 lines each):\n{code}"
    )

def difficulty_based_questions_prompt(code, outline):
    return (
        f"Code Outline:\n{outline}\n\n"
        f"Generate 3 interview questions of varying difficulty:\n"
        f"1. Easy\n2. Medium\n3. Hard\n"
        f"Provide concise answers for each (2-3 lines).\nCode:\n{code}"
    )

def tradeoff_explanation_prompt(code, outline):
    return (
        f"Code Outline:\n{outline}\n\n"
        f"Explain why this solution might be chosen vs alternative approaches.\n"
        f"Discuss trade-offs, pros and cons in 3-4 lines.\nCode:\n{code}"
    )
