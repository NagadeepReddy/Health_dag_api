python3 -B - <<'PY'
from pathlib import Path
import ast

base = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max/cta_max")
clean = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030/artifacts/v1.168-max/cta_max")

for name in ("__init__.py", "live_cta_pipeline_bridge.py", "run_live_max_inference.py"):
    source = base / name
    target = clean / name
    print(f"\n{name}")
    print("ORIGINAL:", "FOUND" if source.is_file() else "MISSING")
    print("CLEAN:", "FOUND" if target.is_file() else "MISSING")

    if source.is_file():
        tree = ast.parse(source.read_text())
        print("IMPORTS:")
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for item in node.names:
                    print(" ", item.name)
            elif isinstance(node, ast.ImportFrom):
                print(" ", "." * node.level + (node.module or ""))

print("\nREAD-ONLY DEPENDENCY CHECK COMPLETE")
PY
