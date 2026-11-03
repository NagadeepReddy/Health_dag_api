set -euo pipefail

ROOT=/application1/sajjna8/rt-pzai-bplan-v1
STAGE=/application1/BPLAN_MAX_FRESH_HANDOFF_TEST_20261102
REL=artifacts/v1.113/lookup/page_seq_2.csv

echo "=== RECOVER EXACT BPLAN LOOKUP FROM GIT ==="

FOUND=0

while IFS= read -r REV; do
  if git -C "$ROOT" cat-file -e "${REV}:${REL}" 2>/dev/null; then
    mkdir -p "$STAGE/artifacts/v1.113/lookup"

    git -C "$ROOT" show "${REV}:${REL}" \
      > "$STAGE/$REL"

    if [ -s "$STAGE/$REL" ]; then
      echo "BPLAN LOOKUP RECOVERED: PASS"
      echo "SOURCE COMMIT: $REV"
      ls -lh "$STAGE/$REL"
      FOUND=1
      break
    fi
  fi
done < <(git -C "$ROOT" log --all --format=%H -- "$REL")

if [ "$FOUND" -eq 0 ]; then
  echo "BPLAN LOOKUP RECOVERY: BLOCKED"
  echo "Required: $REL"
  echo "Obtain the original v1.113 lookup artifact from the model owner."
fi
