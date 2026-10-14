python3 - <<'PY'
import ast
import difflib
from pathlib import Path

base = Path("artifacts/v1.168-max/cta_max")
files = {
    "WORKING_72": base / "grecbase_fusion_order_correct_max.py",
    "OLD_71": base / "grecbase_fusion_seq_isolation_trial.py",
}

blocks = {}

for label, path in files.items():
    source = path.read_text()
    tree = ast.parse(source)
    nodes = [
        node for node in ast.walk(tree)
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        and any(
            isinstance(t, ast.Name) and t.id == "input_types"
            for t in (node.targets if isinstance(node, ast.Assign) else [node.target])
        )
    ]
    if len(nodes) != 1:
        raise SystemExit(f"{label}: expected one input_types assignment, found {len(nodes)}")
    blocks[label] = ast.unparse(nodes[0]).splitlines()

print("=== EXACT INPUT DECLARATION DIFFERENCE ===")
difference = list(difflib.unified_diff(
    blocks["OLD_71"], blocks["WORKING_72"],
    fromfile="OLD_71", tofile="WORKING_72", lineterm=""
))
print("\n".join(difference) if difference else "Declarations identical; difference is elsewhere.")

print("\n=== REMAINING INPUT ASSERTIONS ===")
for label, path in files.items():
    for number, line in enumerate(path.read_text().splitlines(), 1):
        if "len(remaining)" in line:
            print(f"{label}:{number}: {line.strip()}")
PY
