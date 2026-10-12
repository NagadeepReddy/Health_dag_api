python - <<'PY'
import ast
from pathlib import Path

p = Path("artifacts/v1.168/utils/dependency-utils/models.py")
tree = ast.parse(p.read_text())

cls = next(n for n in tree.body
    if isinstance(n, ast.ClassDef)
    and n.name == "ParallelTransformerAEP")

init = next(n for n in cls.body
    if isinstance(n, ast.FunctionDef)
    and n.name == "__init__")

wanted = {
    "ptransformer", "ff1", "seq_pooling_dp",
    "seq_dense", "out_norm1", "out_norm2"
}

for n in ast.walk(init):
    if isinstance(n, (ast.Assign, ast.AnnAssign)):
        targets = n.targets if isinstance(n, ast.Assign) else [n.target]
        for t in targets:
            if isinstance(t, ast.Attribute) and t.attr in wanted:
                print(f"{t.attr}: {ast.unparse(n.value)}")
PY
