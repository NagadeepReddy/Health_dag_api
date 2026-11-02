ROOT=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_max_dev

echo "=== CURRENT MAX INPUT ADAPTER ==="
sed -n '1,125p' "$ROOT/run_real_sanity_input_adapter.py"

echo "=== MAX INFERENCE INPUT CONVERSION ==="
grep -nE 'def infer_max_live|build_real_inputs|runtime_inputs|graph.inputs|model.execute' \
"$ROOT/run_live_max_inference.py"

echo "=== BPLAN GRAPH INPUT DEFINITIONS ==="
sed -n '15,28p' "$ROOT/grecbase_fusion_full_head_72_max.py"
