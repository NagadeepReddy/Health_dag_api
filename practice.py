python3 - <<'PY'
from pathlib import Path
import os

root = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension")
folder = root / "bplan_max_dev/sibling_context_weights"
target = folder / "sibling_context_head.deep_embedding.0.weight.npy"

for name, path in [("FOLDER", folder), ("TARGET", target)]:
    print(f"{name}:", path, flush=True)
    print("  exists:", path.exists(), flush=True)
    print("  symlink:", path.is_symlink(), flush=True)
    print("  resolved:", path.resolve(), flush=True)
    print("  link target:", os.readlink(path) if path.is_symlink() else "none", flush=True)

print("VISIBLE WEIGHT FILES:",
      len(list(folder.glob("*.npy"))) if folder.is_dir() else 0,
      flush=True)
PY
