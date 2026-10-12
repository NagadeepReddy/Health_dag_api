python - <<'PY'
import ast
from pathlib import Path

p = Path("artifacts/v1.168/utils/dependency-utils/models.py")
tree = ast.parse(p.read_text())
cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "GRecBase")
init = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "__init__")

names = {
    "att_pooling", "combined_dim", "extract_deep_idx", "get_path",
    "ihq_embedding", "jet_embedding", "mm_pooling", "moe_norm1",
    "moe_norm2", "nlp_act", "nlp_dense_0", "nlp_dense_1",
    "nlp_encoder", "seq_dense", "sequence_transformer",
    "sibling_context_head", "task_embedding", "task_type_dim"
}

found = set()
for n in ast.walk(init):
    if not isinstance(n, (ast.Assign, ast.AnnAssign)):
        continue
    targets = n.targets if isinstance(n, ast.Assign) else [n.target]
    for t in targets:
        if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id == "self" and t.attr in names:
            print(f"{t.attr}: line {n.lineno}: {ast.unparse(n.value)[:180]}")
            found.add(t.attr)

print("NOT DIRECTLY ASSIGNED IN INIT:", sorted(names - found))
PY
