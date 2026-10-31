ROOT=/application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031

echo "=== PACKAGE SIZE ==="
du -sh "$ROOT"

echo "=== CLEANUP CANDIDATES ==="
find "$ROOT" -type f \( \
  -name '*.bak' -o \
  -name '*.log' -o \
  -name '*.pyc' -o \
  -name '*.tmp' -o \
  -iname '*debug*' -o \
  -iname '*investigation*' \
\) -printf '%P\n' | head -80

echo "=== SYMLINKS ==="
find "$ROOT" -type l -printf '%P -> %l\n'

echo "=== TOP-LEVEL CONTENTS ==="
du -h --max-depth=2 "$ROOT" | sort -hr | head -30

echo "CLEANUP INVENTORY: COMPLETE"
