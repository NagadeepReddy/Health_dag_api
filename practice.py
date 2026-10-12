python - <<'PY'
import ast
from pathlib import Path

base = Path("artifacts/v1.168-max/cta_max")

files = [
    "parallel_transformer_graph_full_sequence.py",
    "nlp_bert_in_graph.py",
    "main_context_max.py",
    "sibling_context_max.py",
    "grecbase_aux_features_max.py",
    "grecbase_get_path_max.py",
]

for name in files:
    p = base / name
    print(f"\n===== {name} =====")

    if not p.exists():
        print("NOT FOUND")
        continue

    tree = ast.parse(p.read_text())

    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            print("FUNCTION:", node.name, ast.unparse(node.args)[:160])

        elif isinstance(node, ast.ClassDef):
            print("CLASS:", node.name)
            for method in node.body:
                if isinstance(method, ast.FunctionDef) and method.name == "__call__":
                    print("  CALL:", ast.unparse(method.args)[:160])

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == "Graph":
                print("  GRAPH:", ast.unparse(node)[:220])

print("\nREAD ONLY — NO FILES MODIFIED")
PY
