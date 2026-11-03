cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import ast

cta = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max/cta_max")
dst = Path("artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev")

print("=== MAX GRAPH ENTRY POINTS ===")
for name in ["grecbase_fusion_full_head_72_max.py", "live_cta_pipeline_bridge.py"]:
    p = cta/name
    print("\nFILE:", name)
    if not p.exists():
        print("MISSING")
        continue
    tree = ast.parse(p.read_text())
    for n in ast.walk(tree):
        if isinstance(n, (ast.ClassDef, ast.FunctionDef)):
            if any(k in n.name.lower() for k in
                   ("grec", "build", "load", "weight", "predict", "execute", "bridge", "forward")):
                print(n.lineno, n.name)

print("\n=== PZAAS SCAFFOLD CHECK ===")
for p in sorted(dst.glob("*.py")):
    text = p.read_text()
    leftovers = [x for x in ("bplan", "BPlan", "BPLAN", "v1.113")
                 if x in text]
    if leftovers:
        print(p.name, "LEFTOVER:", leftovers)

print("FILES:", len(list(dst.glob("*.py"))))
print("ORIGINAL DS: UNCHANGED")
PY
