ORIG=/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/real_max_batch2_backend.py
CLEAN=/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030/batch2/real_max_batch2_backend.py

if [ -f "$ORIG" ] && [ -f "$CLEAN" ]; then
  diff -u "$ORIG" "$CLEAN" | head -120
else
  echo "STOP: File missing"
fi
