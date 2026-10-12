python - <<'PY'
import ast
from pathlib import Path

base = Path("artifacts/v1.168-max/cta_max")

print("=== SEQUENCE INPUT TYPES ===")
p = base / "parallel_transformer_graph_full_sequence.py"
tree = ast.parse(p.read_text())

names = {"int_type", "wide_type", "pos_type"}

for node in ast.walk(tree):
    if isinstance(node, (ast.Assign, ast.AnnAssign)):
        targets = (
            node.targets if isinstance(node, ast.Assign)
            else [node.target]
        )
        if any(
            isinstance(t, ast.Name) and t.id in names
            for t in targets
        ):
            print(ast.unparse(node))

print("\n=== SEQUENCE OUTPUT / PROJECTION ===")
for node in ast.walk(tree):
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == "output":
                print(ast.unparse(node)[:300])

print("\n=== SIBLING INPUT AND POOLING ===")
p = base / "sibling_context_max.py"
tree = ast.parse(p.read_text())

for node in ast.walk(tree):
    if isinstance(node, (ast.Assign, ast.AnnAssign)):
        s = ast.unparse(node)
        if any(k in s.upper() for k in (
            "DEEP_DIMS", "WIDE_DIM", "DEEP_EMBEDDING"
        )):
            print(s[:350])

print("\n=== EXISTING NLP FINAL OUTPUT ===")
p = base / "nlp_bert_in_graph.py"
tree = ast.parse(p.read_text())

for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == "nlp_bert_forward":
        for stmt in node.body[-5:]:
            print(ast.unparse(stmt)[:220])

print("\n=== CURRENT INTEGRATED GRAPH ===")
p = base / "grecbase_fusion_with_context_max.py"
tree = ast.parse(p.read_text())
for node in ast.walk(tree):
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id == "Graph":
            print(ast.unparse(node)[:1300])
            break

print("\nREAD ONLY — NOTHING MODIFIED")
PY
