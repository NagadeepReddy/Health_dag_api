python - <<'PY'
import ast
from pathlib import Path

p = Path("artifacts/v1.168/utils/dependency-utils/models.py")
s = p.read_text()
tree = ast.parse(s)

classes = [
    n for n in ast.walk(tree)
    if isinstance(n, ast.ClassDef) and n.name == "ContextHead"
]
assert len(classes) == 1, "STOP: ContextHead not uniquely found"

methods = [
    n for n in classes[0].body
    if isinstance(n, ast.FunctionDef) and n.name == "forward"
]
assert len(methods) == 1, "STOP: forward not found"

print("===== ORIGINAL CONTEXTHEAD FORWARD =====")
print(ast.get_source_segment(s, methods[0]))
print("===== END =====")
print("NO FILES MODIFIED")
PY
