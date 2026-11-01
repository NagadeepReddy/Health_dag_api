ROOT=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension

ROOT="$ROOT" python3 - <<'PY'
import os, json
from pathlib import Path

root = Path(os.environ["ROOT"])
manifest = json.loads((root / "max_weights/manifest.json").read_text())
mapping = json.loads((root / "bplan_all_90_weight_mapping.json").read_text())["resolved"]

print("=== BPLAN SEQ_DENSE TENSORS ===")
for key, info in manifest.items():
    if "seq_dense" in key:
        print(key, info)

print("\n=== SEQ_DENSE HELPER MAPPINGS ===")
for filename, key in mapping.items():
    if "seq_dense" in filename or "seq_dense" in key:
        print(filename, "->", key)

print("\n=== MAX LAYER USAGE ===")
for name in ("sequence_postprocess_max.py", "grecbase_fusion_full_head_72_max.py"):
    path = root / "bplan_max_dev" / name
    for n, line in enumerate(path.read_text().splitlines(), 1):
        if "seq_dense" in line or "seq_raw" in line:
            print(f"{name}:{n}: {line.strip()}")
PY
