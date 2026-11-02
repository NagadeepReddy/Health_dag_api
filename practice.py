ROOT=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_max_dev

echo "=== WEIGHT REGISTRY ==="
sed -n '88,145p' "$ROOT/run_live_max_inference.py"

echo "=== GRAPH LOAD ==="
sed -n '180,215p' "$ROOT/run_live_max_inference.py"

echo "=== PAGE EMBEDDING ==="
grep -Rn 'sequence_transformer.page_embedding' "$ROOT" --include='*.py'
