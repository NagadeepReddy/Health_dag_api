REPO=/application1/sajjna8/rt-pzai-bplan-v1
EXT="$REPO/artifacts/v1.113-max/maxserve_bplan_extension"
PIPE="$REPO/artifacts/v1.113/core-artifact/pipeline.py"

echo "=== BPLAN JSON ENTRY POINTS ==="
grep -nE 'def (predict_raw|preprocess|postprocess|inference|load)\(' "$PIPE"

echo "=== BPLAN TEST JSON FILES ==="
find "$REPO/artifacts/v1.113" -type f \
  \( -iname '*sanity*.json' -o -iname '*input*.json' -o -iname '*sample*.json' \) | head -20

echo "=== EXISTING BPLAN MAX SERVING FILES ==="
find "$EXT" -maxdepth 3 -type f \
  \( -iname '*serve*.py' -o -iname '*router*.py' -o -iname '*adapter*.py' -o -iname '*launcher*.py' \)
