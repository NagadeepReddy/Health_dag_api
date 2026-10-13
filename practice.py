python - <<'PY'
import ast
from pathlib import Path

root = Path("artifacts/v1.168")
base = Path("artifacts/v1.168-max/cta_max")

p = root / "utils/dependency-utils/models.py"
tree = ast.parse(p.read_text())

print("=== ORIGINAL PYTORCH SEQUENCE ===")
for cls in ast.walk(tree):
    if not isinstance(cls, ast.ClassDef):
        continue
    if "ParallelTransformerMAEP" not in cls.name:
        continue
    print("CLASS:", cls.name)
    for fn in cls.body:
        if isinstance(fn, ast.FunctionDef) and fn.name == "forward":
            print("ARGS:", ast.unparse(fn.args))
            for stmt in fn.body:
                print(ast.unparse(stmt).replace("\n", " ")[:350])

print("\n=== ORIGINAL GRecBase SEQUENCE CALL ===")
for cls in ast.walk(tree):
    if isinstance(cls, ast.ClassDef) and cls.name == "GRecBase":
        for fn in cls.body:
            if isinstance(fn, ast.FunctionDef) and fn.name == "forward":
                for stmt in fn.body:
                    code = ast.unparse(stmt)
                    if "sequence_transformer(" in code or "seq_dense(" in code:
                        print(code[:1200])

print("\n=== CURRENT MAX REAL SEQUENCE PATH ===")
p = base / "grecbase_fusion_real_shapes_max.py"
assert p.is_file()
t = ast.parse(p.read_text())

for fn in t.body:
    if not isinstance(fn, ast.FunctionDef):
        continue
    if "fusion" not in fn.name:
        continue
    for stmt in ast.walk(fn):
        if isinstance(stmt, ast.Assign):
            code = ast.unparse(stmt)
            if any(x in code for x in (
                "features(", "block0(", "block1(",
                "postprocess(", "seq_dense"
            )):
                print(code[:800])

print("\nREAD ONLY — NO FILES MODIFIED")
PY
