DST=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_max_dev

echo "=== BPLAN GRAPH FILES ==="
find "$DST" -maxdepth 1 -type f -name '*.py' -printf '%f\n' | sort

echo "=== GRAPH INPUTS, WEIGHTS AND OUTPUT ==="
grep -nE 'def build_|Graph\(|input_types=|WDIR|BPLAN_BASE_PT|seq_dense|grecbase_integration_weights|graph.output|10438|2048' "$DST"/*.py | head -90
