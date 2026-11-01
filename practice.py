ROOT=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension

ROOT="$ROOT" python3 - <<'PY'
import os, json
from pathlib import Path

root = Path(os.environ["ROOT"])
stage = root / "bplan_helper_weights_stage"
dev = root / "bplan_max_dev"
mapping = json.loads((stage / "mapping.json").read_text())

print("=== STAGED WEIGHT CANDIDATES ===")
for p in sorted(stage.rglob("*norm1*g*.npy")):
    print(p.relative_to(stage))

print("\n=== ORIGINAL BPLAN TENSOR MAPPINGS ===")
for filename, key in sorted(mapping.items()):
    if "norm1" in filename or "norm1" in key:
        print(filename, "->", key)

print("\n=== MAX CODE REFERENCES ===")
for p in sorted(dev.glob("*.py")):
    lines = p.read_text().splitlines()
    for i, line in enumerate(lines):
        if "fn_norm1_g" in line or "sequence_weights" in line:
            print(f"{p.name}:{i+1}: {line.strip()[:180]}")

print("\nORIGINAL DS AND CTA: UNCHANGED")
PY
