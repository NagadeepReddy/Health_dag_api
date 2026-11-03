ROOT=/application1/sajjna8/rt-pzai-bplan-v1

echo "=== EXACT V1.113 LOOKUP CONFIGURATION ==="

grep -n -C 5 -E \
  'lookup_path|model_dir|page_seq_2|file_name|table_path' \
  "$ROOT/artifacts/v1.113/core-artifact/pipeline.py" \
  | head -110

echo "=== V1.113 MODEL CONFIG AND METADATA ==="

find "$ROOT/artifacts/v1.113" \
  -type f \
  \( -name 'init.json' -o -name '*config*.json' -o -name '*lookup*.json' \) \
  ! -path '*/.ipynb_checkpoints/*' \
  -print | head -30

echo "=== ACTUAL V1.113 LOOKUP DIRECTORY ==="

ls -lah "$ROOT/artifacts/v1.113/lookup" 2>&1 || true
