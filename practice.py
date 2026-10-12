python - <<'PY'
import ast
from pathlib import Path

p = Path("artifacts/v1.168/utils/dependency-utils/models.py")
source = p.read_text()
tree = ast.parse(source)

matches = [
    node for node in ast.walk(tree)
    if isinstance(node, ast.ClassDef)
    and node.name == "ParallelTransformerAEP"
]

assert len(matches) == 1, "STOP: Original sequence class not uniquely found"

methods = [
    node for node in matches[0].body
    if isinstance(node, ast.FunctionDef)
    and node.name == "forward"
]

assert len(methods) == 1, "STOP: Original forward not found"

print("===== ORIGINAL SEQUENCE FORWARD =====")
print(ast.get_source_segment(source, methods[0]))
print("===== END =====")
PY
