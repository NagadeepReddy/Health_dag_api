python - <<'PY'
import ast
from pathlib import Path

original = Path("artifacts/v1.168/utils/dependency-utils/models.py")
target = Path("artifacts/v1.168-max/cta_max/grecbase_max.py")

def get_class(path, name):
    tree = ast.parse(path.read_text())
    return next(n for n in tree.body
                if isinstance(n, ast.ClassDef) and n.name == name)

pt = get_class(original, "GRecBase")
mx = get_class(target, "GRecBaseMAX")

forward = next(n for n in pt.body
               if isinstance(n, ast.FunctionDef) and n.name == "forward")
init = next(n for n in mx.body
            if isinstance(n, ast.FunctionDef) and n.name == "__init__")

needed = {
    n.attr for n in ast.walk(forward)
    if isinstance(n, ast.Attribute)
    and isinstance(n.value, ast.Name)
    and n.value.id == "self"
}

available = {
    t.attr
    for n in ast.walk(init)
    if isinstance(n, (ast.Assign, ast.AnnAssign))
    for t in (n.targets if isinstance(n, ast.Assign) else [n.target])
    if isinstance(t, ast.Attribute)
    and isinstance(t.value, ast.Name)
    and t.value.id == "self"
}

print("ORIGINAL FORWARD COMPONENTS:", sorted(needed))
print("MAX INITIALIZED COMPONENTS:", sorted(available))
print("NOT YET INITIALIZED IN MAX:", sorted(needed - available))
PY
