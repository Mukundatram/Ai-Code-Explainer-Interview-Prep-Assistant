import re
import matplotlib.pyplot as plt
from io import BytesIO

def heuristic_time_complexity(code: str) -> str:
    """Estimate time complexity heuristically for any language."""
    loops = len(re.findall(r'\b(for|while|foreach|do)\b', code))
    
    # Detect recursion (generic function calls)
    funcs = re.findall(r'(?:def|function|void|int|float|double|public|private|protected|static)\s+(\w+)\s*\(', code)
    recursion = any(len(re.findall(rf'\b{func}\s*\(', code)) > 1 for func in funcs)

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
    
def get_complexity_level(complexity: str) -> int:
    """Convert complexity string to numerical level for comparison"""
    complexity_levels = {
        'O(1)': 1, 'O(log n)': 2, 'O(n)': 3, 
        'O(n log n)': 4, 'O(n²)': 5, 'O(2ⁿ)': 6, 'O(n!)': 7
    }
    return complexity_levels.get(complexity, 0)

def heuristic_space_complexity(code: str) -> str:
    """Estimate space complexity heuristically for any language."""
    if re.search(r'\[.*\]|new\s+\w+\[', code):
        return "O(n) (Array/List usage)"
    elif re.search(r'(map|dict|hashmap|HashMap)', code, re.IGNORECASE):
        return "O(n) (Map/Dictionary usage)"
    elif re.search(r'(set|HashSet)', code, re.IGNORECASE):
        return "O(n) (Set usage)"
    else:
        return "O(1)"

def generate_complexity_graph(code: str):
    """Generate a bar chart showing time & space complexity."""
    time_c = heuristic_time_complexity(code)
    space_c = heuristic_space_complexity(code)

    def complexity_to_num(c):
        if 'log n' in c:
            return 1.5
        elif 'n log n' in c:
            return 2.5
        elif 'n²' in c or 'n^2' in c:
            return 3
        elif 'n' in c:
            return 2
        return 1

    time_val = complexity_to_num(time_c)
    space_val = complexity_to_num(space_c)

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
