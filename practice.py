python - <<'PY'
import ast
from pathlib import Path

p = Path("artifacts/v1.168-max/cta_max/grecbase_fusion_real_shapes_max.py")
assert p.is_file(), f"Missing: {p}"

lines = p.read_text().splitlines()
tree = ast.parse("\n".join(lines))

print("=== MAX GRAPH OUTPUT AND FINAL LAYERS ===")

for node in ast.walk(tree):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        if node.func.attr == "output":
            start = max(0, node.lineno - 16)
            end = min(len(lines), node.end_lineno + 3)
            for i in range(start, end):
                print(f"{i+1}: {lines[i]}")

print("\n=== GET_PATH / CONCAT / RESHAPE USAGE ===")
for i, line in enumerate(lines, 1):
    if any(x in line for x in (
        "grecbase_get_path_max(",
        "ops.concat(",
        "ops.reshape(",
        "graph.output(",
    )):
        print(f"{i}: {line.strip()}")

print("\nREAD ONLY — NOTHING MODIFIED")
PY
