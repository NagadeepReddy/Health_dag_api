REPO=/application1/sajjna8/rt-pzai-bplan-v1
PIPE="$REPO/artifacts/v1.113/core-artifact/pipeline.py"
EXT="$REPO/artifacts/v1.113-max/maxserve_bplan_extension"

echo "=== JSON INFERENCE AND POSTPROCESS CALLS ==="
grep -nE 'self\.inference\(|self\.postprocess\(|self\.preprocess\(|return json_out_final|def predict_raw' "$PIPE" | tail -45

echo "=== EXISTING MAX SERVING FILES ==="
find "$EXT" -maxdepth 3 -type f \
  \( -name '*router*.py' -o -name '*serve*.py' \
  -o -name '*adapter*.py' -o -name '*launcher*.py' \) \
  | sort
