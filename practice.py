PIPE=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113/core-artifact/pipeline.py

echo "=== ORIGINAL BPLAN INFERENCE ==="
sed -n '1990,2075p' "$PIPE"

echo "=== JSON INTEGRATION POINT ==="
sed -n '4015,4045p' "$PIPE"
