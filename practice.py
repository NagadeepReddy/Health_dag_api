ROOT=/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030

echo "=== SIBLING WEIGHTS IN CLEAN VM ==="
find "$ROOT/batch2" "$ROOT/artifacts/v1.168-max" \
  -name '*sibling*' -print 2>/dev/null | head -60

echo "=== SIBLING WEIGHTS IN ORIGINAL ==="
find /application1/CTA_MAX_TRUE_BATCH2_DEV_20261029 \
  /application1/sajjna8/rt-pzaas-cta-offers-v1 \
  -name '*sibling*' -print 2>/dev/null | head -60
