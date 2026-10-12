python - <<'PY'
import ast
from pathlib import Path

p = Path("artifacts/v1.168/utils/dependency-utils/models.py")
source = p.read_text()
tree = ast.parse(source)

matches = [
    n for n in ast.walk(tree)
    if isinstance(n, ast.ClassDef) and n.name == "GRecBase"
]
assert len(matches) == 1

methods = [
    n for n in matches[0].body
    if isinstance(n, ast.FunctionDef) and n.name == "get_path"
]
assert len(methods) == 1, "STOP: get_path definition differs"

print("===== ORIGINAL GRecBase get_path =====")
print(ast.get_source_segment(source, methods[0]))
print("===== END =====")
print("NO FILES MODIFIED")
PY
