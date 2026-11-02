REPO=/application1/sajjna8/rt-pzai-bplan-v1
PIPE="$REPO/artifacts/v1.113/core-artifact/pipeline.py"
MODELS="$REPO/artifacts/v1.113/utils/dependency-utils/models.py"

echo "=== BPLAN PREDICTION CALL ==="
grep -n -B 12 -A 22 -m 2 'self.bplan_model(' "$PIPE"

echo "=== TRAINED TRANSFER MODEL ARCHITECTURE ==="
grep -n -A 110 'class GRecTransfer' "$MODELS" | head -115

echo "=== BPLAN CHECKPOINTS ==="
find "$REPO/artifacts/v1.113" -type f \
  \( -name 'bplan_model.pt' -o -name 'base_model.pt' \) -print
