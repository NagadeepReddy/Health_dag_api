ROOT=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_max_dev

echo "=== BPLAN MAX SEQUENCE FEATURE CODE ==="
sed -n '1,180p' "$ROOT/sequence_transformer_max.py"

echo "=== BPLAN SEQUENCE WEIGHT SHAPES ==="
grep -nE 'Embedding|Linear|concat|reshape|page|item|50|20' \
"$ROOT/sequence_transformer_max.py"
