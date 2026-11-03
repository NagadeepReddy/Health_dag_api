set -euo pipefail

ARCHIVE=/application1/BPLAN_MAX_SINGLE_REQUEST_HANDOFF_20261102_PORTABLE.tar.gz
STAGE=/application1/BPLAN_MAX_FRESH_HANDOFF_TEST_20261102

cd /application1
sha256sum -c "$(basename "$ARCHIVE").sha256"

if [ -e "$STAGE" ]; then
  echo "STOP: Fresh test directory already exists: $STAGE"
  exit 1
fi

mkdir "$STAGE"
tar -xzf "$ARCHIVE" -C "$STAGE"

STAGE="$STAGE" python3 - <<'PY'
import os
from pathlib import Path

root = Path(os.environ["STAGE"])
required = [
    "artifacts/v1.113/core-artifact/pipeline.py",
    "artifacts/v1.113/core-artifact/base_model.pt",
    "artifacts/v1.113/core-artifact/bplan_model.pt",
    "artifacts/v1.113-max/maxserve_bplan_extension/bplan_native_serve_dev/bplan_native_launcher.py",
]

for name in required:
    assert (root / name).is_file(), f"MISSING: {name}"

links = [p for p in root.rglob("*") if p.is_symlink()]
for link in links:
    assert not os.path.isabs(os.readlink(link)), f"ABSOLUTE LINK: {link}"
    assert link.resolve(strict=True).is_relative_to(root.resolve()), f"UNSAFE LINK: {link}"

weights = list(root.rglob("max_weights/*.npy"))

print("FRESH EXTRACTION: PASS")
print("REQUIRED FILES: PASS")
print("SYMLINK TARGETS: PASS", len(links))
print("MAX NPY WEIGHTS:", len(weights))
print("ISOLATED STAGE:", root)
print("READY FOR FRESH-CONTAINER NATIVE HTTP TEST")
PY
