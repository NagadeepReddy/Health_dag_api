ROOT=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_max_dev

echo "=== FEATURE CLASS LOCATION ==="
grep -Rn 'class ParallelTransformerMAEMAX' "$ROOT" --include='*.py'

echo "=== FEATURE IMPLEMENTATION ==="
grep -Rn -A 110 'class ParallelTransformerMAEMAX' \
  "$ROOT" --include='*.py' | head -115
