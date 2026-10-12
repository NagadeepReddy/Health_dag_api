python - <<'PY'
import ast
from pathlib import Path

base = Path("artifacts/v1.168-max/cta_max")

for filename in (
    "context_head_deep.py",
    "context_head_wide.py",
    "context_head_full.py",
):
    p = base / filename
    source = p.read_text()
    tree = ast.parse(source)

    print(f"\n===== {filename}: FORWARD LOGIC =====")

    for cls in tree.body:
        if isinstance(cls, ast.ClassDef):
            for method in cls.body:
                if (
                    isinstance(method, ast.FunctionDef)
                    and method.name == "__call__"
                ):
                    print("CLASS:", cls.name)
                    print(ast.get_source_segment(source, method))

print("\nREAD-ONLY — NO FILES MODIFIED")
PY
