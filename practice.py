STAGE=/application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031
SAFE=/application1/CTA_MAX_CLEANUP_QUARANTINE_20261031

EXT=artifacts/v1.168-max/cta_native_batch2_release_candidate/maxserve_cta_extension

for REL in \
 "$EXT/cta_native_e2e_test.py" \
 "$EXT/cta_native_startup_test.py" \
 "artifacts/v1.168-max/cta_max/grecbase_integration_weights/seq_dense.weight.npy.before_fix.bak"
do
  if [ -e "$STAGE/$REL" ] && [ ! -e "$SAFE/$REL" ]; then
    mkdir -p "$SAFE/$(dirname "$REL")"
    mv "$STAGE/$REL" "$SAFE/$REL"
    echo "QUARANTINED: $REL"
  fi
done

echo "=== CLEAN PACKAGE CHECK ==="
bash "$STAGE/run_cta_native.sh" check
