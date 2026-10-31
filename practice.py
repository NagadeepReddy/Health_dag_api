SRC=/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max
DST=/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030/artifacts/v1.168-max

echo "=== ROTARY WEIGHT ERROR SOURCE ==="
grep -RFn --include='*.py' \
  'No exported 256-d rotary frequency weights found' \
  "$SRC/cta_max" "$DST/cta_max" 2>/dev/null | head -10

echo "=== ORIGINAL ROTARY/FREQUENCY FILES ==="
find "$SRC/cta_max" -type f \
  \( -iname '*rotary*' -o -iname '*freq*' \) \
  -not -path '*/__pycache__/*' | head -35

echo "=== CLEAN ROTARY/FREQUENCY FILES ==="
find "$DST/cta_max" -type f \
  \( -iname '*rotary*' -o -iname '*freq*' \) \
  -not -path '*/__pycache__/*' | head -35

echo "READ-ONLY CHECK COMPLETE"
