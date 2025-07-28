import ast
import re

def analyze_code_structure_python(code: str) -> dict:
    """Analyze Python code using AST to extract functions, loops, and variables."""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return {"error": f"SyntaxError: {e}"}

    functions = []
    loops = 0
    variables = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            functions.append(node.name)
        elif isinstance(node, (ast.For, ast.While)):
            loops += 1
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            variables.add(node.id)

    return {
        "functions": functions,
        "loops": loops,
        "variables": list(variables)
    }

def analyze_code_structure_generic(code: str) -> dict:
    """
    A naive heuristic for non-Python languages.
    Detects function signatures, loops, and variable-like names.
    """
    # Detect functions (C/Java/JS style)
    functions = re.findall(r'(?:void|int|float|double|public|private|protected|function|def)\s+(\w+)\s*\(', code)
    loops = len(re.findall(r'\b(for|while|foreach|do)\b', code))

    # Variables: detect simple declarations (int x = 0;)
    variables = re.findall(r'\b(?:int|float|double|string|var|let|const)\s+(\w+)', code)

    return {
        "functions": list(set(functions)),
        "loops": loops,
        "variables": list(set(variables))
    }

def generate_outline(code: str, lang: str = "python") -> str:
    """
    Generate a simple outline of the code structure.
    Uses AST for Python, regex heuristics for other languages.
    """
    if lang == "python":
        structure = analyze_code_structure_python(code)
        if "error" in structure:
            return structure["error"]
    else:
        structure = analyze_code_structure_generic(code)

    outline = []
    outline.append(f"Functions: {', '.join(structure['functions']) or 'None'}")
    outline.append(f"Number of Loops: {structure['loops']}")
    outline.append(f"Variables: {', '.join(structure['variables']) or 'None'}")
    return "\n".join(outline)
