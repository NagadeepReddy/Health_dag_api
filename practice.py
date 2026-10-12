python - <<'PY'
import ast
from pathlib import Path

root = Path("artifacts/v1.168")
base = Path("artifacts/v1.168-max/cta_max")

original = root / "utils/dependency-utils/models.py"
current = base / "grecbase_max.py"

def get_class(path, name):
    source = path.read_text()
    tree = ast.parse(source)
    matches = [
        n for n in ast.walk(tree)
        if isinstance(n, ast.ClassDef) and n.name == name
    ]
    assert len(matches) == 1, f"STOP: {name} not uniquely found"
    return source, matches[0]

source, cls = get_class(original, "GRecBase")
forward = next(
    n for n in cls.body
    if isinstance(n, ast.FunctionDef) and n.name == "forward"
)

print("===== ORIGINAL GRecBase EXECUTION ORDER =====")
for node in forward.body:
    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
        continue
    print(ast.unparse(node))

source, cls = get_class(current, "GRecBaseMAX")
print("\n===== CURRENT MAX FORWARD =====")
for node in cls.body:
    if isinstance(node, ast.FunctionDef) and node.name == "__call__":
        print(ast.get_source_segment(source, node))

print("\n===== EXISTING INTEGRATION COMPONENTS =====")
for filename in (
    "parallel_transformer_graph_full_sequence.py",
    "nlp_bert_in_graph.py",
    "main_context_max.py",
    "sibling_context_max.py",
    "grecbase_aux_features_max.py",
    "att_pooling_max.py",
    "grecbase_get_path_max.py",
):
    p = base / filename
    print(filename, "READY" if p.is_file() else "MISSING")

print("\nNO FILES MODIFIED")
PY
