python - <<'PY'
from pathlib import Path
import ast

p = Path(
    "artifacts/v1.168-max/cta_max/"
    "grecbase_fusion_verified_wiring_trial.py"
)

source = p.read_text()
tree = ast.parse(source)

names = {
    "seq", "context", "search0", "search1",
    "task", "jet", "ihq", "sibling",
    "outs", "stage_stacked"
}

print("=== CURRENT FUSION TENSOR PRODUCERS ===")

found = 0
for node in sorted(ast.walk(tree), key=lambda n: getattr(n, "lineno", 0)):
    if isinstance(node, ast.Assign):
        assigned = {
            x.id
            for target in node.targets
            for x in ast.walk(target)
            if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Store)
        }
        if assigned & names:
            found += 1
            print(f"\nLINE {node.lineno} — {', '.join(sorted(assigned & names))}")
            print(ast.get_source_segment(source, node))

print("\n=== ACTUAL GRAPH OUTPUT CONNECTIONS ===")
for node in ast.walk(tree):
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "graph"
        and node.func.attr == "output"
    ):
        for i, arg in enumerate(node.args):
            print(i, ast.unparse(arg))

print("\nASSIGNMENTS FOUND:", found)
print("READ ONLY — NOTHING MODIFIED")
PY
