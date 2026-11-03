set -euo pipefail

BASE=/application1
SOURCE="$BASE/BPLAN_MAX_SINGLE_REQUEST_HANDOFF_20261102_CLEAN.tar.gz"
DEST="$BASE/BPLAN_MAX_TEAM_HANDOFF_20261102"
OUT="$BASE/BPLAN_MAX_TEAM_HANDOFF_20261102.tar.gz"

test -s "$SOURCE"

if [ -e "$DEST" ] || [ -e "$OUT" ]; then
  echo "STOP: Team handoff already exists. Nothing overwritten."
  exit 1
fi

mkdir -p "$DEST"
tar -xzf "$SOURCE" -C "$DEST"

python3 - "$DEST" <<'PY'
from pathlib import Path
from collections import defaultdict
import hashlib, os, sys

root = Path(sys.argv[1]).resolve()
ext = root / "artifacts/v1.113-max/maxserve_bplan_extension"

assert ext.is_dir()
assert (root / "artifacts/v1.113/lookup/aep_seq_2.csv").is_file()

print("=== VERIFY SELF-CONTAINED LINKS ===")

links = [p for p in root.rglob("*") if p.is_symlink()]
bad = [p for p in links
       if not p.exists() or not p.resolve().is_relative_to(root)]

if bad:
    for p in bad[:20]:
        print("UNSAFE LINK:", p, "=>", os.readlink(p))
    raise SystemExit("STOP: External or broken links require review")

print("EXISTING LINKS: PASS")

def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

groups = defaultdict(list)

for p in ext.rglob("*.npy"):
    if p.is_file() and not p.is_symlink():
        groups[digest(p)].append(p)

converted = 0
saved = 0

for hash_value, paths in groups.items():
    if len(paths) < 2:
        continue

    paths.sort(key=lambda p: (
        0 if "max_weights" in p.parts else 1,
        len(p.parts),
        str(p)
    ))

    canonical = paths[0]

    for duplicate in paths[1:]:
        size = duplicate.stat().st_size
        relative = os.path.relpath(canonical, duplicate.parent)
        temporary = duplicate.with_name(
            duplicate.name + ".dedup_temp"
        )

        assert not temporary.exists()

        temporary.symlink_to(relative)

        if digest(temporary) != hash_value:
            temporary.unlink()
            raise RuntimeError("Weight verification failed")

        os.replace(temporary, duplicate)

        assert digest(duplicate) == hash_value
        converted += 1
        saved += size

for p in root.rglob("*"):
    if p.is_symlink():
        assert p.exists()
        assert p.resolve().is_relative_to(root)

print("DUPLICATE WEIGHTS CONSOLIDATED:", converted)
print("DISK SPACE SAVED MB:", round(saved / 1048576, 1))
print("WEIGHT CONTENT PRESERVED: PASS")
print("PORTABLE RELATIVE LINKS: PASS")
print("ORIGINAL DS AND CTA: UNCHANGED")
print("TEAM VM FOLDER:", root)
PY

echo "=== PACKAGE TEAM HANDOFF ==="

tar -C "$DEST" \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='*.log' \
  -czf "$OUT.partial" \
  artifacts/v1.113 \
  artifacts/v1.113-max/maxserve_bplan_extension

gzip -t "$OUT.partial"
mv "$OUT.partial" "$OUT"

sha256sum "$OUT" > "$OUT.sha256"
sha256sum -c "$OUT.sha256"

echo "BPLAN TEAM FOLDER AND ARCHIVE: CREATED"
ls -lh "$OUT" "$OUT.sha256"
