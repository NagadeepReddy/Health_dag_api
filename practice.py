ROOT=/application1/sajjna8/rt-pzai-bplan-v1
STAGE=/application1/BPLAN_MAX_FRESH_HANDOFF_TEST_20261102

echo "=== ORIGINAL TOKENIZER CONFIG ==="
ls -la "$ROOT/artifacts/v1.113/config" 2>&1 || true

echo "=== EXTRACTED TOKENIZER CONFIG ==="
ls -la "$STAGE/artifacts/v1.113/config" 2>&1 || true

echo "=== TOKENIZER PATH REFERENCES ==="
grep -RnE 'debr_path|AutoTokenizer.from_pretrained|artifacts/v1.113/config' \
  "$ROOT/artifacts/v1.113-max/maxserve_bplan_extension" \
  "$ROOT/artifacts/v1.113/core-artifact" \
  --include='*.py' 2>/dev/null | head -25

echo "=== AVAILABLE TOKENIZER FILES ==="
find "$ROOT/artifacts/v1.113" -type f \
  \( -name 'tokenizer_config.json' -o -name 'tokenizer.json' -o -name 'vocab.txt' \) \
  -print | head -25
