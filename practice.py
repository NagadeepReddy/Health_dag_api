cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
import ast
from pathlib import Path

files = {
    "PZAAS": Path("artifacts/v1.472/core-artifact/pipeline.py"),
    "CTA": Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168/core-artifact/pipeline.py")
}

for name, path in files.items():
    print(f"\n=== {name} MODEL INPUTS ===")
    if not path.is_file():
        print("File unavailable:", path)
        continue
    tree = ast.parse(path.read_text())
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            f = node.func
            if isinstance(f.value, ast.Name) and f.value.id == "self":
                if f.attr in ("model_base", "model_sku", "model"):
                    keys = tuple(k.arg for k in node.keywords if k.arg)
                    signature = (f.attr, keys)
                    if signature not in found:
                        found.add(signature)
                        print(f"Line {node.lineno}: {f.attr}")
                        print(f"Inputs ({len(keys)}):", ", ".join(keys))
    if not found:
        print("No direct model calls found")
PY
