import re

def guess_time_complexity(code: str) -> str:
    """
    Universal heuristic-based complexity guesser for multiple languages.
    Detects loops and recursion using language-agnostic patterns.
    """
    # Detect common loop keywords across languages
    loop_patterns = r'\b(for|while|foreach|do)\b'
    loops = len(re.findall(loop_patterns, code))

    # Detect common function definitions (Python, Java, C, C++, JS, etc.)
    func_patterns = r'(?:def|function|void|int|float|double|public|private|protected|static)\s+(\w+)\s*\('
    functions = re.findall(func_patterns, code)

    # Check for recursion (function calling itself)
    recursion_detected = False
    for func in set(functions):
        # More than one occurrence of function name means recursion
        if len(re.findall(rf'\b{func}\s*\(', code)) > 1:
            recursion_detected = True
            break

    # Heuristic complexity estimation
    if recursion_detected and loops > 0:
        return "Possibly O(n * recursion_depth) (Recursion + Loops detected)"
    elif recursion_detected:
        return "Likely O(n) or more (Recursion detected)"
    elif loops >= 2:
        return "Likely O(n^2) or higher (Nested loops detected)"
    elif loops == 1:
        return "Likely O(n) (Single loop detected)"
    else:
        return "Likely O(1) (No loops or recursion detected)"
