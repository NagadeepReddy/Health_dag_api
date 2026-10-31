ROOT=/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030

echo "=== REFERENCE FOLDER DEPENDENCIES ==="

grep -RInE \
  --include='*.py' --include='*.sh' \
  '(/workspace/batch2/cta_max|CTA_MAX_CLEAN_VM_CANDIDATE_20261030/batch2/cta_max|grecbase_aux_branches_batch2_verified|main_context_max_batch2_verified|sibling_context_max_batch2_fix)' \
  "$ROOT/run_cta_native.sh" \
  "$ROOT/artifacts/v1.168-max" \
  2>/dev/null || echo "NO DIRECT REFERENCES FOUND"

echo "=== ACTIVE MODEL PACKAGE ==="
test -f "$ROOT/artifacts/v1.168-max/cta_max/grecbase_fusion_full_head_72_max.py" &&
echo "ACTIVE MODEL: PASS"
