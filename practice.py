ROOT=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension

ROOT="$ROOT" python3 - <<'PY'
import json, os
from pathlib import Path

root = Path(os.environ["ROOT"])
report = json.loads((root / "bplan_helper_weight_mapping.json").read_text())
manifest = json.loads((root / "max_weights/manifest.json").read_text())

for name, candidates in report.items():
    if not candidates:
        print("UNRESOLVED:", name)
        term = Path(name).stem.split("_")[0]
        possible = [k for k in manifest if term in k.lower()]
        print("  POSSIBLE BPLAN TENSORS:", possible[:5])

print("TOTAL UNRESOLVED:", sum(not v for v in report.values()))
PY
