python3 - <<'PY'
import ast
from pathlib import Path

p = Path("artifacts/v1.168/core-artifact/pipeline.py")
tree = ast.parse(p.read_text())

for node in ast.walk(tree):
    if (isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in ("model_base", "model_atc")):
        print("LINE:", node.lineno, "MODEL:", node.func.attr)
        print("KEYWORDS:", [k.arg for k in node.keywords])
        print("POSITIONAL ARGUMENTS:", len(node.args))
PY
