ROOT=/application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031
LINK="$ROOT/artifacts/v1.168-max/cta_max/grecbase_integration_weights/seq_dense.weight.npy.before_fix.bak"
BACKUP=/application1/CTA_MAX_HANDOFF_BACKUP_LINK_20261031

echo "=== EXPECTED BACKUP ==="
ls -ld "$LINK" 2>&1 || true

echo "=== BACKUP DESTINATION ==="
ls -ld "$BACKUP" 2>&1 || true

echo "=== ACTUAL SYMLINKS ==="
find "$ROOT" -type l -printf '%p -> %l\n'
