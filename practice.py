cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import shutil, ast

src = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max/cta_max")
dst = Path("artifacts/v1.472-max/pzaas_max/cta_reference")

names = [
    "grecbase_fusion_full_head_72_max.py",
    "live_cta_pipeline_bridge.py",
]

for name in names:
    if not (src/name).is_file():
        raise SystemExit(f"MISSING SOURCE: {name}")
    if (dst/name).exists():
        raise SystemExit(f"ALREADY EXISTS: {dst/name}")

dst.mkdir(parents=True, exist_ok=True)

for name in names:
    target = dst/name
    shutil.copy2(src/name, target)
    tree = ast.parse(target.read_text())
    print(f"\nCOPIED REFERENCE: {name}")
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            print("IMPORT:", node.module)

print("\nPZAAS GRAPH REFERENCE: READY")
print("PZAAS GRAPH CONVERSION: PENDING")
print("ORIGINAL DS: UNCHANGED")
PY
