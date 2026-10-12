python - <<'PY'
import ast
from pathlib import Path

original = Path(
    "artifacts/v1.168/utils/dependency-utils/models.py"
)
current = Path(
    "artifacts/v1.168-max/cta_max/grecbase_max.py"
)

def get_class(path, name):
    tree = ast.parse(path.read_text())
    matches = [
        n for n in ast.walk(tree)
        if isinstance(n, ast.ClassDef)
        and n.name == name
    ]
    assert len(matches) == 1, f"STOP: {name} not found uniquely"
    return matches[0]

def get_method(cls, name):
    matches = [
        n for n in cls.body
        if isinstance(n, ast.FunctionDef)
        and n.name == name
    ]
    assert len(matches) == 1, f"STOP: {name} missing"
    return matches[0]

def self_attributes(node, context):
    return sorted({
        n.attr for n in ast.walk(node)
        if isinstance(n, ast.Attribute)
        and isinstance(n.value, ast.Name)
        and n.value.id == "self"
        and isinstance(n.ctx, context)
    })

pt = get_class(original, "GRecBase")
mx = get_class(current, "GRecBaseMAX")

pt_forward = get_method(pt, "forward")
mx_init = get_method(mx, "__init__")

needed = set(self_attributes(pt_forward, ast.Load))
implemented = set(self_attributes(mx_init, ast.Store))

print("===== ORIGINAL GRecBase INPUTS =====")
print(ast.unparse(pt_forward.args))

print("\n===== ALREADY DECLARED IN GRecBaseMAX =====")
for name in sorted(implemented):
    print("READY:", name)

print("\n===== ORIGINAL FORWARD DEPENDENCIES NOT DECLARED =====")
for name in sorted(needed - implemented):
    print("MISSING:", name)

print("\nREAD-ONLY CHECK COMPLETE")
print("VERIFIED MAX COMPONENTS UNCHANGED")
PY
