set -euo pipefail

ROOT=/application1/sajjna8/rt-pzai-bplan-v1
OUT=/application1/BPLAN_MAX_SINGLE_REQUEST_HANDOFF_20261102.tar.gz

test -f "$ROOT/artifacts/v1.113/core-artifact/pipeline.py"
test -f "$ROOT/artifacts/v1.113/core-artifact/base_model.pt"
test -f "$ROOT/artifacts/v1.113/core-artifact/bplan_model.pt"
test -f "$ROOT/artifacts/v1.113-max/maxserve_bplan_extension/bplan_native_serve_dev/bplan_native_launcher.py"
test -d "$ROOT/artifacts/v1.113/utils/dependency-utils"

tar -C "$ROOT" \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='*.log' \
  --exclude='.ipynb_checkpoints' \
  -czf "$OUT" \
  artifacts/v1.113/core-artifact \
  artifacts/v1.113/utils \
  artifacts/v1.113-max/maxserve_bplan_extension

sha256sum "$OUT" > "$OUT.sha256"
gzip -t "$OUT"

echo "BPLAN HANDOFF ARCHIVE: PASS"
ls -lh "$OUT" "$OUT.sha256"
