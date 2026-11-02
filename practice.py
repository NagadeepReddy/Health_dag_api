ROOT=/application1/sajjna8/rt-pzai-bplan-v1

echo "=== BPLAN WEIGHT FILE LOCATIONS ==="
find "$ROOT/artifacts" -type f \
  \( -name 'fn_norm1_g.npy' -o -name 'base_model.pt' -o -name 'bplan_model.pt' \) \
  -printf '%p\n'

echo "=== EXPECTED WEIGHTS DIRECTORY ==="
ls -lah "$ROOT/artifacts/v1.113-max/bplan_helper_weights_stage/grecbase_integration_weights" 2>&1 | head -35
