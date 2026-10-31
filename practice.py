ORIG=/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029
CLEAN=/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030

echo "=== REAL MAX BACKEND COMPARISON ==="
find "$ORIG" "$CLEAN" -type f \
  -name 'real_max_batch2_backend.py' \
  -exec sha256sum {} \;
