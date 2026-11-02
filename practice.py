ROOT=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_max_dev

echo "=== BPLAN FEATURE LAYER ==="
sed -n '1,150p' "$ROOT/att_pooling_max.py"

echo "=== BPLAN GRAPH FEATURE CALL ==="
sed -n '15,37p' "$ROOT/grecbase_fusion_full_head_72_max.py"

echo "=== SEQUENCE LENGTH REFERENCES ==="
grep -nE '50|20|concat|reshape|page_wide|def _call_' "$ROOT/att_pooling_max.py"
