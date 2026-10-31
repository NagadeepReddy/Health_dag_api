python3 -B - <<'PY'
from pathlib import Path
import ast

base = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max/cta_max")
clean = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030/artifacts/v1.168-max/cta_max")
p = base / "live_cta_pipeline_bridge.py"

print("ORIGINAL BRIDGE:", p.is_file())
print("CLEAN BRIDGE:", (clean / p.name).is_file())
print("ORIGINAL PACKAGE INIT:", (base / "__init__.py").is_file())
print("CLEAN PACKAGE INIT:", (clean / "__init__.py").is_file())

if p.is_file():
    tree = ast.parse(p.read_text())
    print("\nBRIDGE IMPORTS:")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for item in node.names:
                print("import", item.name)
        elif isinstance(node, ast.ImportFrom):
            print("from", "." * node.level + (node.module or ""), "import", ", ".join(x.name for x in node.names))

print("\nREAD-ONLY CHECK COMPLETE")
PY
