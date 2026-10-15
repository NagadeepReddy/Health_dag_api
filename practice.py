python3 - <<'PY'
import ast
from pathlib import Path

pipeline = ast.parse(Path("artifacts/v1.168/core-artifact/pipeline.py").read_text())
adapter = ast.parse(Path("artifacts/v1.168-max/cta_max/run_real_sanity_input_adapter.py").read_text())

for node in ast.walk(pipeline):
    if (isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "model_base"):
        actual = {k.arg for k in node.keywords if k.arg}
        break
else:
    raise RuntimeError("model_base call not found")

required = {
    n.args[0].value
    for n in ast.walk(adapter)
    if isinstance(n, ast.Call)
    and isinstance(n.func, ast.Name)
    and n.func.id == "get"
    and n.args
    and isinstance(n.args[0], ast.Constant)
    and isinstance(n.args[0].value, str)
}

print("PIPELINE INPUTS:", sorted(actual))
print("MAX EXPECTS:", sorted(required))
print("MISSING IN PIPELINE:", sorted(required - actual))
print("ADDITIONAL PIPELINE INPUTS:", sorted(actual - required))
PY
