cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
import ast
from pathlib import Path

roots = {
    "PZAAS": Path("artifacts/v1.472"),
    "CTA": Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168")
}

for name, root in roots.items():
    print(f"\n=== {name} GREC ARCHITECTURE ===")
    for p in root.rglob("models.py"):
        if "dependency-utils" not in str(p):
            continue
        tree = ast.parse(p.read_text())
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name in ("GRecBase", "GRecTransfer", "GRec"):
                print(f"\nCLASS: {node.name}")
                for method in node.body:
                    if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        print(f"  {method.name}: line {method.lineno}")
                for call in ast.walk(node):
                    if isinstance(call, ast.Call):
                        fn = call.func
                        if isinstance(fn, ast.Attribute) and fn.attr in ("Linear", "Embedding", "MultiheadAttention", "TransformerEncoder"):
                            print(f"  LAYER: {fn.attr} at line {call.lineno}")
                break
PY
