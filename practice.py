cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import json

root = Path("artifacts/v1.472-max/pzaas_max")
weights = root / "pzaas_base_weights"
manifest = json.loads((weights / "manifest.json").read_text())
target = root / "pzaas_weight_loader.py"

if target.exists():
    raise SystemExit("STOP: Loader already exists")

if len(manifest) != 208:
    raise SystemExit("STOP: Unexpected tensor count")

missing = [
    k for k, v in manifest.items()
    if not (weights / v["file"]).is_file()
]
if missing:
    raise SystemExit(f"Missing weights: {missing[:5]}")

code = '''
from pathlib import Path
import json
import numpy as np

WEIGHTS = Path(__file__).resolve().parent / "pzaas_base_weights"
MANIFEST = json.loads((WEIGHTS / "manifest.json").read_text())

def load_weight(name, expected_shape=None):
    if name not in MANIFEST:
        raise KeyError(f"PZAAS weight missing: {name}")

    entry = MANIFEST[name]
    path = (WEIGHTS / entry["file"]).resolve()

    if path.parent != WEIGHTS.resolve():
        raise ValueError("Invalid weight path")

    array = np.load(path, mmap_mode="r", allow_pickle=False)

    if expected_shape is not None:
        if tuple(array.shape) != tuple(expected_shape):
            raise ValueError(
                f"{name}: expected {expected_shape}, got {array.shape}"
            )

    return array
'''

compile(code, str(target), "exec")
target.write_text(code)

print("PZAAS WEIGHT LOADER: CREATED")
print("EXPORTED WEIGHTS VERIFIED:", len(manifest))
print("MAX GRAPH WIRING: PENDING")
print("ORIGINAL DS: UNCHANGED")
PY
