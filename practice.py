ROOT=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never \
  --entrypoint python3 \
  -v "$ROOT:/bplan:ro" \
  -v /application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031:/cta:ro \
  localhost/cta-max-faiss:local - <<'PY'
import json
import numpy as np
from pathlib import Path
from collections import Counter

root = Path("/bplan")
cta = Path("/cta/artifacts/v1.168-max/cta_max")
data = json.loads((root / "bplan_all_90_weight_mapping.json").read_text())

assert len(data["resolved"]) == 90
assert not data["ambiguous"] and not data["missing"]

counts = Counter()

for filename, key in sorted(data["resolved"].items()):
    cta_file = cta / filename
    bplan_file = root / "max_weights" / f"{key}.npy"

    if not cta_file.is_file() or not bplan_file.is_file():
        counts["MISSING FILE"] += 1
        print("MISSING FILE:", filename, key)
        continue

    expected = np.load(cta_file, mmap_mode="r")
    actual = np.load(bplan_file, mmap_mode="r")

    if actual.shape == expected.shape:
        status = "SAME SHAPE"
    elif actual.ndim == 2 and actual.T.shape == expected.shape:
        status = "TRANSPOSE CANDIDATE"
    else:
        status = "DIFFERENT SHAPE"

    counts[status] += 1

    if status != "SAME SHAPE":
        print(status, filename,
              "CTA:", expected.shape,
              "BPLAN:", actual.shape)

print("\n=== BPLAN 90 WEIGHT SHAPE AUDIT ===")
for status, count in sorted(counts.items()):
    print(status + ":", count)
print("TOTAL:", sum(counts.values()))
print("ORIGINAL DS AND CTA: UNCHANGED")
PY
