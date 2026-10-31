bash <<'SH'
set -euo pipefail

ROOT=/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030
REF="$ROOT/batch2/cta_max"
BACKUP=/application1/CTA_MAX_CLEAN_VM_REFERENCE_HELD_20261031
success=0

if [ ! -d "$REF" ] || [ -e "$BACKUP" ]; then
  echo "STOP: Reference missing or backup exists"
  exit 1
fi

trap '
if [ "$success" != 1 ] && [ -d "$BACKUP" ] && [ ! -e "$REF" ]; then
  mv "$BACKUP" "$REF"
  echo "ROLLBACK: Reference restored"
fi
' EXIT

mv "$REF" "$BACKUP"

echo "=== LAUNCHER CHECK ==="
bash "$ROOT/run_cta_native.sh" check

echo "=== HTTP WITHOUT DUPLICATE ==="
python3 -B - "$ROOT" <<'PY'
import sys, json, urllib.request
from pathlib import Path

root = Path(sys.argv[1])
src = root / "artifacts/v1.168-max/cta_native_adjusted_sanity_input.json"

req = urllib.request.Request(
    "http://127.0.0.1:18767/v2/cta/predict",
    data=src.read_bytes(),
    headers={"Content-Type": "application/json"},
    method="POST"
)

with urllib.request.urlopen(req, timeout=180) as r:
    result = json.load(r)
    assert r.status == 200
    assert result and not (
        isinstance(result, dict) and "error" in result
    )
    print("HTTP 200: PASS")
    print("CTA JSON: PASS")
PY

success=1
echo "DUPLICATE REFERENCE ISOLATION: PASS"
echo "Backup safely retained outside clean package"
SH
