ROOT=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension

echo "=== BPLAN WEIGHT LOCATIONS ==="
find "$ROOT" -name '*remove_tasks_dense1*' -print

echo "=== MAX HELPER WEIGHT PATH ==="
sed -n '1,32p' \
"$ROOT/bplan_max_dev/grecbase_get_path_max.py"

echo "=== ORIGINAL BPLAN CHECKPOINT ==="
ls -lh /application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113/core-artifact/base_model.pt
