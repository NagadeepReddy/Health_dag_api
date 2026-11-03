cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import json
from collections import Counter

root = Path("artifacts/v1.472-max/pzaas_max")
manifest = json.loads(
    (root/"pzaas_base_weights/manifest.json").read_text()
)

print("=== PZAAS TRAINED WEIGHT GROUPS ===")
groups = Counter(k.split(".")[0] for k in manifest)
for name, count in sorted(groups.items()):
    print(f"{name}: {count}")

print("\n=== MAX GRAPH WEIGHT LOADING SITES ===")
for p in sorted(root.glob("*.py")):
    if p.name == "pzaas_weight_loader.py":
        continue
    lines = p.read_text().splitlines()
    hits = [
        (i, line.strip())
        for i, line in enumerate(lines, 1)
        if any(x in line for x in (
            "np.load(", "WDIR =", "WEIGHTS =",
            "WEIGHT_DIR", "cta_max/",
            "v1.168", "pzaas_base_weights"
        ))
    ]
    if hits:
        print(f"\n{p.name}")
        for i, line in hits[:12]:
            print(f"  {i}: {line[:160]}")

print("\nWEIGHT MAPPING INSPECTION: COMPLETE")
print("NO FILES MODIFIED")
PY
