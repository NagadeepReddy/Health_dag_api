DST=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_max_dev

echo "=== BPLAN GRAPH DIMENSION LOCATIONS ==="
grep -RnE --include='*.py' \
'256, 512|512, 256|3506|3146|10727|10094|10438|2048|EXPECTED_FEATURES|fused_dims|input_types=|seq_dense|graph.output' \
"$DST" | grep -v '__pycache__' | head -85
