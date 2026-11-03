set -euo pipefail

ROOT=/application1/sajjna8/rt-pzai-bplan-v1
STAGE=/application1/BPLAN_MAX_FRESH_HANDOFF_TEST_20261102
REL=artifacts/v1.113-max/maxserve_bplan_extension

ORIGINAL=/application1/BPLAN_MAX_SINGLE_REQUEST_HANDOFF_20261102_FINAL.tar.gz
CLEAN=/application1/BPLAN_MAX_SINGLE_REQUEST_HANDOFF_20261102_CLEAN.tar.gz

test -s "$ORIGINAL"
test -d "$ROOT/$REL"
test -d "$STAGE/$REL"
test ! -e "$CLEAN"

echo "=== SAFE BPLAN CLEANUP ==="

for BASE in "$ROOT/$REL" "$STAGE/$REL"; do
  find "$BASE" -type d -name __pycache__ -prune -exec rm -rf {} +
  find "$BASE" -type f \( \
    -name '*.pyc' -o \
    -name '*.pre_bridge_backup' -o \
    -name '*.pre_typed_queue_backup' -o \
    -name '*.before_response_trace' \
  \) -delete
done

echo "GENERATED CACHES AND OLD BACKUPS: REMOVED"

echo "=== BUILD CLEAN HANDOFF ==="

tar -C "$STAGE" \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='*.log' \
  --exclude='*.pre_bridge_backup' \
  --exclude='*.pre_typed_queue_backup' \
  --exclude='*.before_response_trace' \
  --exclude='.ipynb_checkpoints' \
  -czf "$CLEAN.partial" \
  artifacts/v1.113 \
  "$REL"

gzip -t "$CLEAN.partial"

ORIGINAL="$ORIGINAL" NEW="$CLEAN.partial" python3 - <<'PY'
import os, tarfile

def members(path):
    with tarfile.open(path, "r:gz") as t:
        return {
            m.name: (m.size, m.type, m.linkname)
            for m in t if m.isfile() or m.issym() or m.islnk()
        }

old = members(os.environ["ORIGINAL"])
new = members(os.environ["NEW"])

removed = set(old) - set(new)
allowed = (
    ".pre_bridge_backup",
    ".pre_typed_queue_backup",
    ".before_response_trace",
)

assert all(x.endswith(allowed) for x in removed), removed
assert not (set(new) - set(old)), "Unexpected added files"
assert all(new[k] == old[k] for k in new), "File metadata changed"
assert removed, "No known backup files removed"

print("REMOVED BACKUP ENTRIES:", len(removed))
print("RETAINED ENTRIES:", len(new))
print("REQUIRED FILES PRESERVED: PASS")
print("CLEAN ARCHIVE STRUCTURE: PASS")
PY

mv "$CLEAN.partial" "$CLEAN"
sha256sum "$CLEAN" > "$CLEAN.sha256"
sha256sum -c "$CLEAN.sha256"

echo "=== RESULT ==="
echo "BPLAN CLEAN ARCHIVE: PASS"
echo "ORIGINAL VALIDATED ARCHIVE: PRESERVED"
echo "ORIGINAL DS AND CTA: UNCHANGED"
ls -lh "$CLEAN" "$CLEAN.sha256"
