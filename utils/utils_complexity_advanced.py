import radon.complexity as rcc
import ast
import re
import networkx as nx
from io import BytesIO
import matplotlib.pyplot as plt


def cyclomatic_complexity_report(code: str, lang='python'):
    """Compute cyclomatic complexity using radon (only for Python)."""
    if lang != 'python':
        return "Cyclomatic complexity not supported for this language."
    try:
        analysis = rcc.cc_visit(code)
        report_lines = [f"Function `{block.name}`: Complexity {block.complexity}" for block in analysis]
        return "\n".join(report_lines) if report_lines else "No functions detected."
    except Exception as e:
        return f"Error in complexity analysis: {e}"


def heuristic_time_complexity(code: str, debug=False) -> str:
    """
    Heuristic-based time complexity estimation for any language.
    """
    # Count loops
    loops = len(re.findall(r'\b(for|while|foreach|do)\b', code))

    # Detect possible functions (generic for multiple languages)
    funcs = re.findall(r'\b([A-Za-z_]\w*)\s*\(', code)
    keywords_to_ignore = {'if', 'for', 'while', 'switch', 'return', 'catch', 'else'}
    funcs = [f for f in funcs if f not in keywords_to_ignore]

    recursion = False
    for func in set(funcs):
        if len(re.findall(rf'\b{func}\s*\(', code)) > 1:
            recursion = True
            break

    if debug:
        print(f"Detected loops: {loops}")
        print(f"Detected functions: {funcs}")
        print(f"Recursion detected: {recursion}")

    if re.search(r'\.sort\(|sorted\(|Arrays\.sort\(|Collections\.sort\(', code):
        return "O(n log n)"
    elif recursion and loops:
        return "O(n * recursion_depth)"
    elif recursion:
        return "O(n) or more (Recursion)"
    elif loops >= 2:
        return "O(n²) or higher (Nested loops)"
    elif loops == 1:
        return "O(n)"
    else:
        return "O(1)"


def heuristic_space_complexity(code: str, debug=False) -> str:
    """
    Heuristic-based space complexity estimation for any language.
    """
    list_like = re.search(r'\[.*\]|new\s+\w+\[|\{.*:.*\}', code)
    map_like = re.search(r'(map|dict|hashmap|HashMap)', code, re.IGNORECASE)
    set_like = re.search(r'(set|HashSet)', code, re.IGNORECASE)

    if debug:
        print(f"List-like detected: {bool(list_like)}")
        print(f"Map-like detected: {bool(map_like)}")
        print(f"Set-like detected: {bool(set_like)}")

    if list_like:
        return "O(n) (Array/List/Collection usage)"
    elif map_like:
        return "O(n) (Map/Dictionary usage)"
    elif set_like:
        return "O(n) (Set usage)"
    else:
        return "O(1)"


def generate_complexity_graph(code: str):
    """
    Generate a bar chart comparing time and space complexity.
    """
    time_c = heuristic_time_complexity(code)
    space_c = heuristic_space_complexity(code)

    def complexity_to_num(c):
        if 'n log n' in c:
            return 2.5
        elif 'n²' in c or 'n^2' in c:
            return 3
        elif 'n' in c:
            return 2
        return 1

    time_val = complexity_to_num(time_c)
    space_val = complexity_to_num(space_c)

    # Plot bar chart with annotations
    plt.figure(figsize=(5, 4))
    bars = plt.bar(['Time Complexity', 'Space Complexity'],
                   [time_val, space_val],
                   color=['skyblue', 'lightgreen'])

    for bar, label in zip(bars, [time_c, space_c]):
        plt.text(bar.get_x() + bar.get_width() / 2,
                 bar.get_height() + 0.1,
                 label, ha='center', fontsize=9, color='black')

    plt.title('Complexity Estimation')
    plt.ylim(0, 3.5)
    plt.ylabel('Complexity Level (1=O(1), 2=O(n), 3=O(n²))')
    plt.tight_layout()

    # Save to memory instead of a file
    buf = BytesIO()
    plt.savefig(buf, format="png")
    plt.close()
    buf.seek(0)

    return buf, time_c, space_c

def generate_function_call_graph(code: str, lang='python'):
    """
    Generate a function call graph using AST (Python only) and return it as a memory buffer.
    """
    if lang != 'python':
        return None
    try:
        tree = ast.parse(code)
        graph = nx.DiGraph()
        func_defs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
        for func in func_defs:
            graph.add_node(func.name)
            for node in ast.walk(func):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    graph.add_edge(func.name, node.func.id)

        if not graph.nodes:
            return None

        # Create graph plot
        plt.figure(figsize=(6, 4))
        pos = nx.spring_layout(graph)
        nx.draw_networkx_nodes(graph, pos, node_color='lightblue', node_size=1500)
        nx.draw_networkx_edges(graph, pos, arrowstyle='->', arrowsize=12)
        nx.draw_networkx_labels(graph, pos, font_size=10, font_family='sans-serif')
        plt.axis('off')

        # Save to buffer instead of disk
        buf = BytesIO()
        plt.savefig(buf, format="png")
        plt.close()
        buf.seek(0)
        return buf

    except Exception:
        return None
