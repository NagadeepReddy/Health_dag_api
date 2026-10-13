python - <<'PY'
import ast
from pathlib import Path

orig = Path("artifacts/v1.168/utils/dependency-utils/models.py")
base = Path("artifacts/v1.168-max/cta_max")

print("=== ORIGINAL SEQUENCE VL USAGE ===")
tree = ast.parse(orig.read_text())

for cls in ast.walk(tree):
    if isinstance(cls, ast.ClassDef) and cls.name == "ParallelTransformerMAEP":
        for fn in cls.body:
            if isinstance(fn, ast.FunctionDef) and fn.name == "forward":
                print("ARGS:", ast.unparse(fn.args))
                lines = orig.read_text().splitlines()
                refs = sorted({
                    n.lineno for n in ast.walk(fn)
                    if isinstance(n, ast.Name) and n.id == "vl_in"
                })
                print("VL REFERENCES:", refs)
                for line in refs:
                    for i in range(max(fn.lineno, line-2),
                                   min(fn.end_lineno, line+2)+1):
                        print(f"{i}: {lines[i-1]}")

print("\n=== MAX SEQUENCE FEATURE IMPLEMENTATION ===")
found = 0
for p in base.glob("*.py"):
    if "class ParallelTransformerMAEPMAX" not in p.read_text():
        continue
    t = ast.parse(p.read_text())
    for cls in t.body:
        if isinstance(cls, ast.ClassDef) and cls.name == "ParallelTransformerMAEPMAX":
            found += 1
            print("FILE:", p.name)
            for fn in cls.body:
                if isinstance(fn, ast.FunctionDef) and fn.name == "__call__":
                    print("ARGS:", ast.unparse(fn.args))
                    for stmt in fn.body:
                        print(ast.unparse(stmt).replace("\n", " ")[:450])

print("MAX FEATURE CLASSES FOUND:", found)

print("\n=== REAL FUSION SEQUENCE CALL ===")
p = base / "grecbase_fusion_real_shapes_max.py"
assert p.is_file()
t = ast.parse(p.read_text())
for n in ast.walk(t):
    if isinstance(n, ast.Call) and ast.unparse(n.func) == "features":
        print("LINE:", n.lineno)
        print("CALL:", ast.unparse(n))

print("\nREAD ONLY — NO FILES MODIFIED")
PY
