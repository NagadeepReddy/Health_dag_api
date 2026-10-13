python - <<'PY'
import ast
from pathlib import Path

original = Path("artifacts/v1.168/utils/dependency-utils/models.py")
maxfile = Path("artifacts/v1.168-max/cta_max/sibling_context_max.py")

assert original.is_file() and maxfile.is_file()

tree = ast.parse(original.read_text())

print("=== ORIGINAL PYTORCH SIBLING HEAD ===")
found = 0

for cls in ast.walk(tree):
    if not isinstance(cls, ast.ClassDef):
        continue
    methods = {
        n.name: n for n in cls.body
        if isinstance(n, ast.FunctionDef)
    }
    if "forward" not in methods:
        continue

    class_text = ast.unparse(cls)
    if "num_batch_norm" not in class_text or "deep_embedding" not in class_text:
        continue

    found += 1
    print("CLASS:", cls.name)
    for stmt in methods["forward"].body:
        code = ast.unparse(stmt).replace("\n", " ")
        print(" ", code[:350])

print("MATCHING PYTORCH CLASSES:", found)

print("\n=== EXISTING MAX SIBLING HEAD ===")
mt = ast.parse(maxfile.read_text())

func = next(
    n for n in mt.body
    if isinstance(n, ast.FunctionDef)
    and n.name == "sibling_context_forward"
)

for stmt in func.body:
    if isinstance(stmt, ast.FunctionDef):
        print("HELPER:", stmt.name)
        for part in stmt.body:
            code = ast.unparse(part).replace("\n", " ")
            print(" ", code[:250])
    else:
        code = ast.unparse(stmt).replace("\n", " ")
        print(" ", code[:350])

print("\nREAD ONLY — NO FILES MODIFIED")
PY
