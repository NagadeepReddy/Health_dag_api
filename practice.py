ROOT=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension

ROOT="$ROOT" python3 - <<'PY'
import os, json
from pathlib import Path

root = Path(os.environ["ROOT"])
manifest = json.loads((root / "max_weights/manifest.json").read_text())

print("=== BPLAN PAGE EMBEDDING WEIGHTS ===")
for name in manifest:
    if "page_embedding" in name:
        print(name, manifest[name])

print("\n=== MAX GRAPH WEIGHT REGISTRATION ===")
for file in sorted((root / "bplan_max_dev").glob("*.py")):
    for line_no, line in enumerate(file.read_text().splitlines(), 1):
        if ("page_embedding" in line or
            "weights_registry" in line or
            "weights_registry" in line or
            "WeightsRegistry" in line):
            print(f"{file.name}:{line_no}: {line.strip()[:180]}")

print("\nORIGINAL DS AND CTA: UNCHANGED")
PY
