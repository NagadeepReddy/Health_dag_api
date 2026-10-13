python - <<'PY'
import ast
from pathlib import Path

root = Path("artifacts/v1.168")
base = Path("artifacts/v1.168-max/cta_max")

original = root / "utils/dependency-utils/models.py"
max_aux = base / "grecbase_aux_branches_max.py"
max_graph = base / "grecbase_fusion_verified_wiring_trial.py"

terms = ("task", "ihq", "jet", "sibling")

for p in (original, max_aux, max_graph):
    if not p.is_file():
        raise SystemExit(f"STOP: Missing source: {p}")

print("=== ORIGINAL PYTORCH GRecBase.forward — AUXILIARY BRANCHES ===")

source = original.read_text()
tree = ast.parse(source)
classes = [
    n for n in tree.body
    if isinstance(n, ast.ClassDef) and n.name == "GRecBase"
]
if len(classes) != 1:
    raise SystemExit("STOP: GRecBase class not uniquely found")

methods = [
    n for n in classes[0].body
    if isinstance(n, ast.FunctionDef) and n.name == "forward"
]
if len(methods) != 1:
    raise SystemExit("STOP: GRecBase.forward not uniquely found")

for node in methods[0].body:
    snippet = ast.get_source_segment(source, node) or ""
    if any(t in snippet.lower() for t in terms):
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.Expr)):
            print(f"\nLINE {node.lineno}:\n{snippet[:2200]}")

print("\n=== MAX AUXILIARY BRANCH IMPLEMENTATION ===")

source = max_aux.read_text()
tree = ast.parse(source)
for node in tree.body:
    if isinstance(node, ast.FunctionDef) and (
        node.name == "grecbase_aux_features"
    ):
        print(ast.get_source_segment(source, node))

print("\n=== MAX ACTUAL AUXILIARY INPUT CONNECTIONS ===")

source = max_graph.read_text()
tree = ast.parse(source)
for node in ast.walk(tree):
    if isinstance(node, ast.Assign):
        lhs = ", ".join(ast.unparse(t) for t in node.targets)
        if any(t in lhs.lower() for t in terms):
            if node.lineno <= 80:
                print(
                    f"LINE {node.lineno}: "
                    f"{ast.get_source_segment(source, node)}"
                )

print("\nREAD ONLY — NO MODEL FILES MODIFIED")
PY
