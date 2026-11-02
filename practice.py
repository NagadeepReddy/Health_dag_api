ROOT=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension

echo "=== BPLAN MAX GRAPH (FULL) ==="
nl -ba "$ROOT/bplan_max_dev/grecbase_fusion_full_head_72_max.py"

echo "=== BPLAN MAX ADAPTER (GRAPH SETUP) ==="
sed -n '1,125p' "$ROOT/bplan_max_dev/bplan_max_model_adapter.py"

echo "=== BPLAN BATCH-2 SOURCE INSPECTION COMPLETE ==="
