set -euo pipefail

STAGE=/application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031
SAFE=/application1/CTA_MAX_CLEANUP_QUARANTINE_20261031

KEEP="$STAGE/artifacts/v1.168-max/real_max_batch2_backend.py"
DUP="$STAGE/batch2/real_max_batch2_backend.py"

test -f "$KEEP" && test -f "$DUP"
cmp -s "$KEEP" "$DUP"

grep -qF '$ART/real_max_batch2_backend.py' \
  "$STAGE/run_cta_native.sh"

test ! -e "$SAFE/real_max_batch2_backend.py"

mkdir -p "$SAFE"

mv "$DUP" "$SAFE/real_max_batch2_backend.py"

echo "=== CHECK CLEAN PACKAGE ==="
if bash "$STAGE/run_cta_native.sh" check; then
    echo "DUPLICATE BACKEND QUARANTINED: PASS"
    echo "ORIGINAL WORKING CODE: UNCHANGED"
else
    mv "$SAFE/real_max_batch2_backend.py" "$DUP"
    echo "CLEANUP ROLLED BACK"
fi
