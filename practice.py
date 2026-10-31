bash <<'SH'
set -euo pipefail

ROOT=/application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031
LINK="$ROOT/artifacts/v1.168-max/cta_max/grecbase_integration_weights/seq_dense.weight.npy.before_fix.bak"
BACKUP=/application1/CTA_MAX_HANDOFF_BACKUP_LINK_20261031

if [ ! -L "$LINK" ] || [ -e "$BACKUP" ] || [ -L "$BACKUP" ]; then
  echo "STOP: Backup symlink missing or destination occupied"
  exit 1
fi

if grep -RIlF \
  --include='*.py' --include='*.sh' \
  'seq_dense.weight.npy.before_fix.bak' \
  "$ROOT" | grep -q .; then
  echo "STOP: Backup referenced by code"
  exit 1
fi

mv "$LINK" "$BACKUP"

if bash "$ROOT/run_cta_native.sh" check; then
  echo "BACKUP SYMLINK ISOLATED: PASS"
  echo "ORIGINAL RUNNING CODE: UNCHANGED"
else
  mv "$BACKUP" "$LINK"
  echo "ROLLBACK: Backup restored"
  exit 1
fi
SH
