python - <<'PY'
import ast
from pathlib import Path

base = Path("artifacts/v1.168-max/cta_max")

print("=== SEQUENCE GRAPH INPUT CONTRACT ===")
p = base / "parallel_transformer_graph_full_sequence.py"
src = p.read_text()
tree = ast.parse(src)

for node in ast.walk(tree):
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id == "Graph":
            print(ast.unparse(node)[:2400])

print("\n=== SEQUENCE COMPONENT CONSTRUCTION ===")
for node in ast.walk(tree):
    if isinstance(node, ast.Assign):
        if any(
            isinstance(t, ast.Name) and t.id in
            ("features", "block0", "block1", "postprocess")
            for t in node.targets
        ):
            print(ast.unparse(node)[:700])

print("\n=== SIBLING INPUT CONTRACT ===")
p = base / "sibling_context_max.py"
src = p.read_text()
tree = ast.parse(src)

for node in ast.walk(tree):
    if isinstance(node, ast.Assign):
        text = ast.unparse(node)
        if any(x in text.upper() for x in
               ("DEEP_DIMS", "WIDE_DIM", "DEEP_EMBEDDING")):
            print(text[:500])

for p in sorted(base.glob("run*sibling*.py"))[:2]:
    tree = ast.parse(p.read_text())
    print("RUNNER:", p.name)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "Graph":
                print("GRAPH:", ast.unparse(node)[:1800])

print("\n=== ORIGINAL MODEL NLP ACTIVATION ===")
p = Path("artifacts/v1.168/utils/dependency-utils/models.py")
src = p.read_text()
for term in ("nlp_act1", "nlp_dense1"):
    print(term, "occurrences:", src.count(term))

print("\nNO FILES MODIFIED")
PY
