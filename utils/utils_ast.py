# Updated utils_ast.py
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

def get_first_function_name(code: str) -> str | None:
    """
    Extract the name of the first function definition in the Python code using AST.
    """
    try:
        tree = ast.parse(code)
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                return node.name
        return None
    except SyntaxError:
        return None

def execute_instrumented_code(code_str, input_value):
    """
    Execute the user code, locate the first function definition, wrap it so every
    call is recorded in `calls` (args, depth, index, parent_index, result, memoized),
    then invoke it with input_value and return the call trace.
    """
    try:
        # Parse the code and ensure there's a function
        tree = ast.parse(code_str)
        if not tree.body:
            return None, "Error: No valid code provided."

        func_name = get_first_function_name(code_str)
        if not func_name:
            return None, "Error: No function definition found in the code."

        # Execute the user code in a fresh namespace
        exec_globals = {}
        exec(compile(tree, "<string>", "exec"), exec_globals)

        if func_name not in exec_globals:
            return None, "Error: Function not found after execution."

        original_func = exec_globals[func_name]

        # Trace containers
        calls = []
        call_counter = {"count": 0}
        parent_stack = []
        memo = {}  # cache for memoization

        # Wrapper factory - will intercept every call (including recursive ones)
        def make_wrapper(f):
            def wrapper(*args, **kwargs):
                idx = call_counter["count"]
                call_counter["count"] += 1
                depth = len(parent_stack)
                parent_idx = parent_stack[-1] if parent_stack else None

                # Normalize args for dict key
                key = (args, tuple(sorted(kwargs.items())))
                memoized = key in memo

                # Store simple representation of args
                simple_args = []
                for a in args:
                    if isinstance(a, (int, float, str, bool, type(None))):
                        simple_args.append(a)
                    else:
                        try:
                            simple_args.append(repr(a))
                        except Exception:
                            simple_args.append(str(type(a)))

                calls.append((simple_args, depth, idx, parent_idx, None, memoized))
                parent_stack.append(idx)

                if memoized:
                    result = memo[key]
                else:
                    result = f(*args, **kwargs)
                    memo[key] = result

                parent_stack.pop()
                # Update recorded result
                calls[idx] = (calls[idx][0], calls[idx][1], calls[idx][2], calls[idx][3], result, memoized)
                return result
            return wrapper

        # Create wrapper, replace the name in globals so recursive calls hit wrapper
        wrapped_func = make_wrapper(original_func)
        exec_globals[func_name] = wrapped_func

        # Call the wrapped function with the input value
        if isinstance(input_value, (list, tuple)):
            result = wrapped_func(*input_value)
        else:
            result = wrapped_func(input_value)

        return calls, None

    except Exception as e:
        return None, f"Error: {str(e)}"