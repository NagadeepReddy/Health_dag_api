python3 - <<'PY'
import ast
import difflib
from pathlib import Path

base = Path("artifacts/v1.168-max/cta_max")
files = {
    "WORKING_72": base / "grecbase_fusion_order_correct_max.py",
    "OLD_71": base / "grecbase_fusion_seq_isolation_trial.py",
}

def extract(path):
    source = path.read_text()
    tree = ast.parse(source)
    found = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, "attr", "")
        if name != "Graph":
            continue
        for kw in node.keywords:
            if kw.arg == "input_types":
                found.append((node.lineno, ast.unparse(kw.value)))

    return found

results = {label: extract(path) for label, path in files.items()}

for label, items in results.items():
    print(f"\n=== {label} ===")
    print("Graph input_types definitions:", len(items))
    for line, expr in items:
        print("Graph starts at line:", line)
        print("Expression characters:", len(expr))

if all(len(items) == 1 for items in results.values()):
    old = results["OLD_71"][0][1]
    new = results["WORKING_72"][0][1]

    old_lines = old.replace(" + [", "\n+ [").splitlines()
    new_lines = new.replace(" + [", "\n+ [").splitlines()

    print("\n=== EXACT GRAPH INPUT DIFFERENCE ===")
    diff = list(difflib.unified_diff(
        old_lines, new_lines,
        fromfile="OLD_71", tofile="WORKING_72",
        lineterm=""
    ))
    print("\n".join(diff[:100]) if diff else "Input definitions identical")
else:
    print("\nGraph definitions need a different comparison; no changes made.")

print("\nOriginal files: UNCHANGED")
PY
