STAGE=/application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031

echo "=== POSSIBLE DUPLICATE BACKEND ==="
sha256sum \
 "$STAGE/batch2/real_max_batch2_backend.py" \
 "$STAGE/artifacts/v1.168-max/real_max_batch2_backend.py"

echo "=== CHECK FILE DEPENDENCIES ==="
grep -RInE \
 --include='*.py' \
 --include='*.sh' \
 --include='*.txt' \
 'cta_native_e2e_test|cta_native_startup_test|run_real_sanity_input_adapter|run_live_max_inference|run_batch2_contract|before_fix.bak|real_max_batch2_backend' \
 "$STAGE" 2>/dev/null | head -80

echo "CLEANUP DEPENDENCY AUDIT COMPLETE"
