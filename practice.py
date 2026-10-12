python - <<'PY'
import ast
from pathlib import Path

base = Path("artifacts/v1.168-max/cta_max")

for filename in ("context_head_full.py", "context_head_base_max.py"):
    p = base / filename
    assert p.is_file(), f"STOP: Missing {p}"
    source = p.read_text()
    tree = ast.parse(source)

    print(f"\n===== {filename} =====")

    for cls in tree.body:
        if not isinstance(cls, ast.ClassDef):
            continue

        print("CLASS:", cls.name)

        for node in cls.body:
            if isinstance(node, ast.FunctionDef):
                if node.name in ("__init__", "__call__"):
                    print("METHOD:", ast.unparse(node.args))
                    if node.name == "__call__":
                        print(ast.get_source_segment(source, node))

original = Path(
    "artifacts/v1.168/utils/dependency-utils/models.py"
)
source = original.read_text()
tree = ast.parse(source)

cls = next(
    n for n in ast.walk(tree)
    if isinstance(n, ast.ClassDef) and n.name == "GRecBase"
)

forward = next(
    n for n in cls.body
    if isinstance(n, ast.FunctionDef) and n.name == "forward"
)

print("\n===== ORIGINAL CONTEXTHEAD CALLS =====")

for n in ast.walk(forward):
    if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
        if n.func.attr in ("context_head", "sibling_context_head"):
            print(ast.get_source_segment(source, n))

print("\nREAD-ONLY — NO FILES MODIFIED")
PY
