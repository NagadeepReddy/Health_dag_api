STAGE=/application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031
SAFE=/application1/CTA_MAX_CLEANUP_QUARANTINE_20261031

USED="$STAGE/artifacts/v1.168-max/real_max_batch2_backend.py"
EXTRA="$STAGE/batch2/real_max_batch2_backend.py"
BACKUP="$SAFE/real_max_batch2_backend.py"

echo "=== SAFE BACKEND CLEANUP ==="

if [ ! -f "$USED" ] || [ ! -f "$EXTRA" ]; then
  echo "STOP: Required files missing"
elif [ -e "$BACKUP" ]; then
  echo "STOP: Quarantine destination occupied"
elif ! grep -Fq '$ART/real_max_batch2_backend.py' "$STAGE/run_cta_native.sh"; then
  echo "STOP: Launcher reference not confirmed"
else
  mkdir -p "$SAFE"
  if mv "$EXTRA" "$BACKUP"; then
    if bash "$STAGE/run_cta_native.sh" check; then
      echo "CLEAN BACKEND CLEANUP: PASS"
      echo "PORTABLE BACKEND: PRESERVED"
      echo "ORIGINAL CODE: UNCHANGED"
    else
      mv "$BACKUP" "$EXTRA"
      echo "CLEANUP ROLLED BACK"
    fi
  else
    echo "STOP: Move failed"
  fi
fi
