REPO=/application1/sajjna8/rt-pzai-bplan-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never \
  --entrypoint python3 \
  -v "$REPO:$REPO:ro" -w "$REPO" \
  localhost/cta-max-faiss:local -B - <<'PY'
from pathlib import Path
import numpy as np

root = Path("artifacts/v1.113-max/maxserve_bplan_extension")

for folder in (
    root / "max_weights",
    root / "grecbase_integration_weights",
    root / "bplan_max_dev/sequence_weights",
):
    print("\nDIRECTORY:", folder, "EXISTS:", folder.is_dir())
    if folder.is_dir():
        for file in sorted(folder.rglob("*.npy")):
            if "rotary" in file.name.lower() or "inv_freq" in file.name.lower():
                arr = np.load(file, mmap_mode="r")
                print("WEIGHT:", file, "SHAPE:", arr.shape)

adapter = root / "bplan_max_dev/run_real_sanity_input_adapter.py"
print("\n=== ADAPTER ROTARY CONFIG ===")
for i, line in enumerate(adapter.read_text().splitlines(), 1):
    if 65 <= i <= 100:
        print(f"{i}: {line}")
PY
