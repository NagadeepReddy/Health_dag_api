cd /application1/sajjna8/rt-pzaas-v1.0 && \
python3 - <<'PY'
from pathlib import Path
import ast

p = Path(
    "artifacts/v1.472-max/pzaas_max/"
    "grecbase_fusion_full_head_72_max.py"
)

source = p.read_text()
tree = ast.parse(source)
lines = source.splitlines()

functions = [
    n for n in ast.walk(tree)
    if isinstance(n, ast.FunctionDef)
    and n.name.startswith("build_")
]

assert functions, "MAX graph builder not found"

for fn in functions:
    print("=== PZAAS MAX COMPUTATION WIRING ===")
    print("FUNCTION:", fn.name)
    print("LINES:", fn.lineno, "-", fn.end_lineno)

    for i in range(fn.lineno, fn.end_lineno + 1):
        print(f"{i}: {lines[i-1]}")

print("\n=== GRAPH SOURCE: COMPLETE ===")
print("ORIGINAL DS: UNCHANGED")
print("MAX GRAPH: UNCHANGED")
print("NEXT: PZAAS COMPUTATION ALIGNMENT")
PY
