ROOT=/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030/artifacts/v1.168-max/cta_max

echo "=== ACTUAL WEIGHT PATHS ==="
ls -ld "$ROOT/grecbase_integration_weights" "$ROOT/sequence_weights"

echo "=== RESOLVED LOCATIONS ==="
readlink -f "$ROOT/grecbase_integration_weights"
readlink -f "$ROOT/sequence_weights"

echo "=== ROTARY WEIGHT ==="
find "$ROOT" -name 'att_pooling.rotary_emb_inv_freq.npy' -print
