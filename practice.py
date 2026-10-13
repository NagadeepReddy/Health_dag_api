cd /application/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

python - <<'PY'
import ast
from pathlib import Path

root = Path("artifacts/v1.168-max/cta_max")
found = False

for p in root.rglob("*.py"):
    source = p.read_text()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        continue

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "ParallelTransformerMeanMAX":
            found = True
            print("FILE:", p)
            for method in node.body:
                if isinstance(method, ast.FunctionDef) and method.name in ("__call__", "forward"):
                    print(ast.get_source_segment(source, method))

if not found:
    print("STOP: Feature class not found; no changes made")
PY
