STAGE=/application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031
SAFE=/application1/CTA_MAX_CLEANUP_QUARANTINE_20261031

echo "=== CLEANUP DIAGNOSIS ==="

for f in \
 "$STAGE/artifacts/v1.168-max/real_max_batch2_backend.py" \
 "$STAGE/batch2/real_max_batch2_backend.py" \
 "$SAFE/real_max_batch2_backend.py" \
 "$STAGE/run_cta_native.sh"; do
  if [ -f "$f" ]; then
    echo "FOUND: $f"
  else
    echo "MISSING: $f"
  fi
done

echo "=== BACKEND COMPARISON ==="
sha256sum \
 "$STAGE/artifacts/v1.168-max/real_max_batch2_backend.py" \
 "$STAGE/batch2/real_max_batch2_backend.py" 2>&1

echo "=== LAUNCHER REFERENCE ==="
grep -n 'real_max_batch2_backend' \
 "$STAGE/run_cta_native.sh" || true

echo "DIAGNOSIS COMPLETE"
