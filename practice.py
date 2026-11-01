ROOT=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never \
  --entrypoint python3 \
  -v "$ROOT:/bplan:rw" \
  localhost/cta-max-faiss:local - <<'PY'
import json, numpy as np
from pathlib import Path

root = Path("/bplan")
data = json.loads((root / "bplan_all_90_weight_mapping.json").read_text())
mapping = data["resolved"]
dst = root / "bplan_helper_weights_stage"

assert len(mapping) == 90
assert not data["ambiguous"] and not data["missing"]
assert not dst.exists(), "STOP: staging folder already exists"

# Validate everything before writing
items = []
for name, key in sorted(mapping.items()):
    src = root / "max_weights" / f"{key}.npy"
    assert src.is_file(), f"Missing: {src}"
    arr = np.load(src, allow_pickle=False)
    assert np.issubdtype(arr.dtype, np.number), name
    assert np.isfinite(arr).all(), name
    items.append((name, key, arr))

for name, key, arr in items:
    target = dst / name
    target.parent.mkdir(parents=True, exist_ok=True)
    np.save(target, arr, allow_pickle=False)

(dst / "mapping.json").write_text(json.dumps(mapping, indent=2))

print("BPLAN WEIGHT STAGING: PASS")
print("EXPORTED:", len(items))
print("LOCATION:", dst)
print("ORIGINAL DS AND CTA: UNCHANGED")
print("GRAPH ADAPTATION: STILL REQUIRED")
PY
