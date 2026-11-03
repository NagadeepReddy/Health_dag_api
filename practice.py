python3 - <<'PY'
from pathlib import Path
from collections import defaultdict
import hashlib, tarfile, os

root = Path("/application1/sajjna8/rt-pzai-bplan-v1")
stage = Path("/application1/BPLAN_MAX_FRESH_HANDOFF_TEST_20261102")
archive = Path("/application1/BPLAN_MAX_SINGLE_REQUEST_HANDOFF_20261102_FINAL.tar.gz")
rel = Path("artifacts/v1.113-max/maxserve_bplan_extension")

print("=== BPLAN CLEANUP AUDIT ===")

for name, path in [
    ("ORIGINAL INTEGRATION", root / rel),
    ("VALIDATED HANDOFF", stage / rel),
    ("FINAL ARCHIVE", archive),
]:
    print(name, "PASS" if path.exists() else "MISSING", path)

print("\n=== INTEGRATION FOLDERS ===")
for base in (root / rel, stage / rel):
    if base.exists():
        print("\n", base)
        for p in sorted(base.iterdir()):
            print(" ", p.name, "(directory)" if p.is_dir() else "(file)")

print("\n=== POSSIBLE UNNECESSARY FILES ===")
found = 0
for base in (root / rel, stage / rel):
    if not base.exists():
        continue
    for p in base.rglob("*"):
        if not p.is_file():
            continue
        n = p.name.lower()
        if any(x in n for x in (
            "backup", ".bak", ".tmp", ".log",
            "debug", "trace", "investigation",
            ".pyc", ".orig", ".swp"
        )) or "__pycache__" in p.parts:
            print(p)
            found += 1
print("CANDIDATES:", found)

print("\n=== DUPLICATE SMALL INTEGRATION FILES ===")
for base in (root / rel, stage / rel):
    if not base.exists():
        continue
    hashes = defaultdict(list)
    for p in base.rglob("*"):
        if p.is_file() and not p.is_symlink() and p.stat().st_size <= 2_000_000:
            h = hashlib.sha256(p.read_bytes()).hexdigest()
            hashes[h].append(str(p.relative_to(base)))
    for names in hashes.values():
        if len(names) > 1:
            print("IN:", base)
            print("DUPLICATE CONTENT:", names)

print("\n=== SYMLINK INTEGRITY ===")
for p in stage.rglob("*"):
    if p.is_symlink():
        target = p.resolve()
        if not target.exists() or not target.is_relative_to(stage.resolve()):
            print("NEEDS REVIEW:", p, "=>", os.readlink(p))

print("\n=== FINAL ARCHIVE CONTENT CHECK ===")
if archive.is_file():
    with tarfile.open(archive, "r:gz") as t:
        names = t.getnames()
        print("ARCHIVE ENTRIES:", len(names))
        print("INTEGRATION PYTHON FILES:",
              sum(n.endswith(".py") and "maxserve_bplan_extension" in n for n in names))
        junk = [n for n in names if
                "__pycache__" in n or n.endswith((".log", ".pyc", ".tmp", ".bak"))]
        print("ARCHIVED JUNK:", len(junk))
        for n in junk[:15]:
            print(" ", n)

print("\nBPLAN CLEANUP AUDIT COMPLETE — NO FILES MODIFIED")
PY
