python - <<'PY'
import ast
from pathlib import Path

root = Path("artifacts/v1.168")
base = Path("artifacts/v1.168-max/cta_max")

original = ast.parse(
    (root/"utils/dependency-utils/models.py").read_text()
)
maxfile = base/"main_context_max.py"
tree = ast.parse(maxfile.read_text())

print("=== ORIGINAL MAIN CONTEXT FORWARD ===")
for cls in ast.walk(original):
    if not isinstance(cls, ast.ClassDef):
        continue
    if cls.name != "ContextHead":
        continue
    for node in cls.body:
        if isinstance(node, ast.FunctionDef) and node.name == "forward":
            for stmt in node.body:
                print(ast.unparse(stmt).replace("\n", " ")[:500])

print("\n=== MAX MAIN CONTEXT OPERATIONS ===")
for fn in tree.body:
    if not isinstance(fn, ast.FunctionDef):
        continue
    if "context" not in fn.name.lower():
        continue
    print("FUNCTION:", fn.name)
    for stmt in fn.body:
        if isinstance(stmt, ast.Assign):
            target = ast.unparse(stmt.targets[0])
            if target in ("deep", "wide"):
                print(ast.unparse(stmt).replace("\n", " ")[:350])

print("\n=== SIBLING FIX CONFIRMATION ===")
p = base/"sibling_context_max.py"
text = p.read_text()
print("FIXED FILE EXISTS:", p.is_file())
print("BACKUP EXISTS:", p.with_name(
    "sibling_context_max.py.before_activation_fix.bak"
).is_file())

print("\nREAD ONLY — NO FILES MODIFIED")
PY
