python3 - <<'PY'
from pathlib import Path
import subprocess

root = Path("/application1")
name = "fn_normal_8.npy"

print("CHECKING REQUIRED MAX WEIGHT")
found = []

for base in [
    root / "sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max",
    root / "CTA_MAX_TRUE_BATCH2_DEV_20261029",
    root / "cta_max_true_batch_dev_20261028",
]:
    if base.is_dir():
        found.extend(base.rglob(name))

for p in found:
    print("FOUND:", p)

if not found:
    print("BLOCKED: Required weight not found in known workspaces")
else:
    print("WEIGHT FOUND: PASS")

print("ORIGINAL DS/MAX: UNCHANGED")
print("CONTAINERS RESTARTED: NONE")
PY
