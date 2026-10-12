python - <<'PY'
import ast
from pathlib import Path

base = Path("artifacts/v1.168-max/cta_max")

for filename in ("context_head_deep.py", "context_head_wide.py"):
    p = base / filename
    source = p.read_text()
    tree = ast.parse(source)

    print(f"\n===== {filename} CONSTRUCTORS =====")

    for cls in tree.body:
        if not isinstance(cls, ast.ClassDef):
            continue

        for node in cls.body:
            if isinstance(node, ast.FunctionDef) and node.name == "__init__":
                print("CLASS:", cls.name)
                print(ast.get_source_segment(source, node))

print("\nREAD-ONLY — NO FILES MODIFIED")
PY
