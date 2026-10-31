ROOT=/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030
ORIG=/application1/sajjna8/rt-pzaas-cta-offers-v1

echo "=== AVAILABLE ROTARY FILES ==="
find "$ROOT/artifacts/v1.168-max" \
     "$ORIG/artifacts/v1.168-max" \
     -name '*rotary*.npy' -print 2>/dev/null

echo "=== CLEAN DESTINATION ==="
ls -ld "$ROOT/artifacts/v1.168-max/cta_max/sequence_weights"
