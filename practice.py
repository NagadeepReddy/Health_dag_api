ROOT=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_max_dev

echo "=== GRAPH IMPORTS ==="
sed -n '1,17p' "$ROOT/grecbase_fusion_full_head_72_max.py"

echo "=== FEATURE CLASS REFERENCES ==="
grep -RniE 'ParallelTransformerMAE|class .*MAE|def features|def forward' \
  "$ROOT" --include='*.py' | head -50

echo "=== FEATURE MODULE FILES ==="
find "$ROOT" -maxdepth 2 -type f \
  \( -iname '*feature*' -o -iname '*sequence*' -o -iname '*transformer*' \)
