REPO=/application1/sajjna8/rt-pzai-bplan-v1
PIPE="$REPO/artifacts/v1.113/core-artifact/pipeline.py"
DEV="$REPO/artifacts/v1.113-max/maxserve_bplan_extension/bplan_max_dev"

echo "=== ORIGINAL MODEL LOADING ==="
grep -n -A 65 -E 'def loadModel\(|def loadBaseModel\(|def load\(' "$PIPE" | head -155

echo "=== EXISTING MAX RUNTIME ENTRY ==="
sed -n '1,90p' "$DEV/run_live_max_inference.py"

echo "=== MAX EXECUTION AND WEIGHT REGISTRY ==="
grep -nE 'def |session.load|model.execute|weights_registry|runtime_inputs' \
"$DEV/run_live_max_inference.py" | tail -35
