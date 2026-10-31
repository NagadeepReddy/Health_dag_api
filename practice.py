CLEAN=/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030/artifacts/v1.168-max
ORIG=/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max

for ROOT in "$CLEAN" "$ORIG"; do
  echo "=== $ROOT ==="
  find "$ROOT" -type f -name 'seq_dense_weight.npy' -print
done

echo "=== EXPECTED CLEAN PATH ==="
ls -lh "$CLEAN/cta_max/grecbase_integration_weights/seq_dense_weight.npy" 2>&1
