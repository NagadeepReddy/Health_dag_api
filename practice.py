bash <<'SH'
set -euo pipefail

ROOT=/application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031
LINK="$ROOT/artifacts/v1.168-max/cta_max/grecbase_integration_weights.link_backup"

if [ ! -L "$LINK" ]; then
  echo "STOP: Expected symlink not found"
  exit 1
fi

if grep -RIlF \
  --include='*.py' --include='*.sh' \
  'grecbase_integration_weights.link_backup' \
  "$ROOT" | grep -q .; then
  echo "STOP: Symlink referenced by code"
  exit 1
fi

test "$(readlink "$LINK")" = "sequence_weights" || {
  echo "STOP: Unexpected symlink target"
  exit 1
}

unlink "$LINK"

bash "$ROOT/run_cta_native.sh" check

echo "UNUSED STAGE SYMLINK REMOVED: PASS"
echo "ORIGINAL WORKING CONTAINER: UNCHANGED"
SH
