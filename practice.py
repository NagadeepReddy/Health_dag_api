python - <<'PY'
import ast
from pathlib import Path

base = Path("artifacts/v1.168-max/cta_max")

for filename in ["sequence_transformer_max.py", "grecbase_max.py"]:
    p = base / filename
    source = p.read_text()
    tree = ast.parse(source)

    print(f"\n===== {filename} =====")

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            print("CLASS:", node.name)
            for method in node.body:
                if isinstance(method, ast.FunctionDef) and method.name == "__call__":
                    print(ast.get_source_segment(source, method))
PY
