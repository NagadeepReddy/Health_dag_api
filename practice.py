set -euo pipefail

STAGE=/application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031
OUT=/application1/CTA_MAX_TEAM_HANDOFF_CLEAN_20261031.tar.gz

test -d "$STAGE"
test ! -e "$OUT"

bash "$STAGE/run_cta_native.sh" check

if find "$STAGE" -type l -print -quit | grep -q .; then
  echo "STOP: Symlinks require verification"
  exit 1
fi

echo "=== CREATING CLEAN ARCHIVE ==="
tar -czf "$OUT" -C /application1 \
  CTA_MAX_TEAM_HANDOFF_STAGE_20261031

echo "=== VERIFY ARCHIVE ==="
tar -tzf "$OUT" >/dev/null
sha256sum "$OUT"
du -h "$OUT"

echo "CLEAN HANDOFF ARCHIVE: PASS"
