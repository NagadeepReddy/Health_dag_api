ORIG=/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029
CLEAN=/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030

echo "=== WORKER ADAPTER COMPARISON ==="

find "$ORIG" "$CLEAN" \
  -type f -name 'cta_worker_adapter.py' \
  -exec sha256sum {} \;

echo "=== NATIVE LAUNCHER FILES ==="

find "$ORIG" "$CLEAN" \
  -type f \( -name '*launcher*.py' -o -name 'cta_native_batch2_backend.py' \) \
  -print
