ORIG=/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/grecbase_fusion_full_head_72_max.py
CLEAN=/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030/artifacts/v1.168-max/cta_max/grecbase_fusion_full_head_72_max.py

if [ -f "$ORIG" ] && [ -f "$CLEAN" ]; then
  sha256sum "$ORIG" "$CLEAN"
  diff -u "$ORIG" "$CLEAN" | head -80
else
  echo "STOP: Source or clean file missing"
fi
