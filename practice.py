ROOT=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension

cat > "$ROOT/bplan_max_dev/bplan_weights.py" <<'PY'
from pathlib import Path
import json
import numpy as np

WEIGHT_DIR = Path(__file__).resolve().parent.parent / "max_weights"
MANIFEST = json.loads(
    (WEIGHT_DIR / "manifest.json").read_text()
)

def load_weight(name, expected_shape=None):
    if name not in MANIFEST:
        raise KeyError(f"BPLAN weight missing: {name}")

    path = WEIGHT_DIR / f"{name}.npy"
    arr = np.load(path, allow_pickle=False)

    actual = tuple(arr.shape)
    declared = tuple(MANIFEST[name]["shape"])

    if actual != declared:
        raise ValueError(f"{name}: manifest shape mismatch")

    if expected_shape is not None:
        if actual != tuple(expected_shape):
            raise ValueError(
                f"{name}: expected {expected_shape}, got {actual}"
            )

    return arr

def validate():
    assert len(MANIFEST) == 208
    for name in MANIFEST:
        load_weight(name)
    return len(MANIFEST)
PY

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --entrypoint python3 \
  -v "$ROOT:/bplan:ro" \
  -w /bplan/bplan_max_dev \
  localhost/cta-max-faiss:local \
  -c "from bplan_weights import validate; print('BPLAN MAX WEIGHT LOADER: PASS', validate())"
