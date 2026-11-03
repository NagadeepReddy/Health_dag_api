cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import ast

root = Path("artifacts/v1.472-max/pzaas_max/cta_reference")

for name in [
    "grecbase_fusion_full_head_72_max.py",
    "live_cta_pipeline_bridge.py"
]:
    p = root/name
    print(f"\n=== {name} ===")
    s = p.read_text().splitlines()
    tree = ast.parse("\n".join(s))

    print("FUNCTIONS / CLASSES:")
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.ClassDef)):
            print(f"  {n.lineno}: {n.name}")

    print("\nGRAPH / WEIGHT DEPENDENCIES:")
    count = 0
    for i, line in enumerate(s, 1):
        if any(x in line.lower() for x in [
            "weight_dir", "weight_path", ".npy",
            "2048", "10819", "72_input",
            "graph(", "tensor(", "shape=",
            "cta_max", "grecbase_integration"
        ]):
            print(f"{i}: {line.strip()[:160]}")
            count += 1
            if count >= 45:
                break
PY
