ROOT=/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030

echo "=== DUPLICATE FOLDER SIZES ==="
du -sh "$ROOT/batch2/cta_max" \
       "$ROOT/artifacts/v1.168-max/cta_max"

echo "=== SYMLINKS ==="
find "$ROOT/artifacts/v1.168-max" -type l -print

echo "=== HARDCODED VM PATHS ==="
grep -RInE \
  --include='*.py' --include='*.sh' \
  '/application1/|CTA_MAX_TRUE_BATCH2_DEV' \
  "$ROOT/artifacts/v1.168-max" 2>/dev/null | head -35

echo "=== LAUNCHER FILES ==="
find "$ROOT" -type f \
  \( -name '*launcher*.py' -o -name '*.sh' \) \
  -print | head -30
