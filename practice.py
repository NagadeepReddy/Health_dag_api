ROOT=/application1/sajjna8/rt-pzai-bplan-v1
STAGE=/application1/BPLAN_MAX_FRESH_HANDOFF_TEST_20261102

echo "=== RESTORE ORIGINAL V1.113 LOOKUPS ==="
mkdir -p "$STAGE/artifacts/v1.113/lookup"
cp -an "$ROOT/artifacts/v1.113/lookup/." \
  "$STAGE/artifacts/v1.113/lookup/"

echo "=== VERIFY CORRECT SOURCE FILE ==="
ls -lh \
  "$ROOT/artifacts/v1.113/lookup/aep_seq_2.csv" \
  "$STAGE/artifacts/v1.113/lookup/aep_seq_2.csv"

echo "=== FIND INCORRECT FILENAME REFERENCES ==="
grep -RnF 'page_seq_2.csv' \
  "$ROOT/artifacts/v1.113/core-artifact" \
  "$ROOT/artifacts/v1.113-max/maxserve_bplan_extension" \
  "$STAGE/artifacts/v1.113-max/maxserve_bplan_extension" \
  --include='*.py' 2>/dev/null | head -30 || true

echo "=== VERIFY ORIGINAL CONFIGURATION ==="
grep -n -C 3 'aep_seq_2.csv' \
  "$ROOT/artifacts/v1.113/core-artifact/pipeline.py" | head -30

echo "BPLAN LOOKUP STAGING COMPLETE"
