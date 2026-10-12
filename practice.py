python - <<'PY'
import ast
from pathlib import Path

p = Path("artifacts/v1.168/core-artifact/pipeline.py")
lines = p.read_text().splitlines()
tree = ast.parse(p.read_text())

def show(a, b):
    for n in range(max(1, a), min(len(lines), b) + 1):
        print(f"{n}: {lines[n-1]}")

for node in ast.walk(tree):
    if not isinstance(node, ast.FunctionDef):
        continue

    if node.name == "predict_raw":
        print("===== REAL INPUT CREATION AND INFERENCE CALL =====")
        locations = set()

        for n in ast.walk(node):
            if isinstance(n, ast.Call):
                name = ast.unparse(n.func)
                if "preprocess" in name or name.endswith(".inference"):
                    locations.add(n.lineno)

            if isinstance(n, (ast.Assign, ast.AnnAssign)):
                targets = n.targets if isinstance(n, ast.Assign) else [n.target]
                if any(
                    isinstance(t, ast.Name) and t.id == "model_in"
                    for t in targets
                ):
                    locations.add(n.lineno)

        shown = set()
        for location in sorted(locations):
            for i in range(max(node.lineno, location - 7),
                           min(node.end_lineno, location + 7) + 1):
                if i not in shown:
                    print(f"{i}: {lines[i-1]}")
                    shown.add(i)
            print("---")

    if node.name == "preprocess":
        print("===== PREPROCESS RETURN CONTRACT =====")
        returns = [
            n for n in ast.walk(node)
            if isinstance(n, ast.Return)
        ]
        for r in returns[-3:]:
            show(r.lineno - 3, r.end_lineno)

print("\nREAD ONLY — NO FILES MODIFIED")
PY
