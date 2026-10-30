for f in \
/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/native_batch2_minimal_overlay/cta_worker_adapter.py \
/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/native_batch2/cta_worker_adapter.py
do
  if [ -f "$f" ]; then
    echo "=== $f ==="
    sed -n '55,120p' "$f"
  fi
done
