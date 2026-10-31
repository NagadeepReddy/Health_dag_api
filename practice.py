ORIG=/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029
CLEAN=/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030

for DIR in "$ORIG" "$CLEAN"; do
  echo "=== $DIR ==="
  find "$DIR" -type f \( \
    -name 'grecbase_fusion_full_head_72_max.py' -o \
    -name 'cta_worker_adapter.py' -o \
    -name 'cta_native_batch2_backend.py' -o \
    -name 'seq_dense_weight.npy' \
  \) -print 2>/dev/null
done
