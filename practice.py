python - <<'PY'
import ast
from pathlib import Path

base = Path("artifacts/v1.168-max/cta_max")

targets = {
    "parallel_transformer_graph_full_sequence.py":
        "build_parallel_transformer_graph",
    "nlp_bert_in_graph.py": "nlp_bert_forward",
    "main_context_max.py": "main_context_forward",
    "sibling_context_max.py": "sibling_context_forward",
    "grecbase_aux_features_max.py": "grecbase_aux_features",
}

for filename, name in targets.items():
    p = base / filename
    print(f"\n===== {filename} =====")

    if not p.exists():
        print("MISSING FILE")
        continue

    source = p.read_text()
    tree = ast.parse(source)
    methods = [
        n for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef) and n.name == name
    ]

    if not methods:
        print("FUNCTION NOT FOUND")
        continue

    node = methods[0]
    print("ARGS:", ast.unparse(node.args))

    lines = source.splitlines()
    print("FINAL IMPLEMENTATION LINES:")

    start = max(node.lineno, node.end_lineno - 11)
    for i in range(start, node.end_lineno + 1):
        print(f"{i}: {lines[i-1]}")

print("\nREAD ONLY — NO FILES MODIFIED")
PY
