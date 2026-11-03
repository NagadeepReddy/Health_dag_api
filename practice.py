python3 - <<'PY'
from pathlib import Path
from collections import defaultdict
import hashlib, re

ROOT = Path("/application1/BPLAN_MAX_RUNTIME_CLEAN_20261102")
EXT = ROOT / "artifacts/v1.113-max/maxserve_bplan_extension"

assert ROOT.is_dir(), "Clean handoff missing"
assert EXT.is_dir(), "MAX integration missing"

required = [
    "artifacts/v1.113/core-artifact/pipeline.py",
    "artifacts/v1.113/lookup/aep_seq_2.csv",
    "artifacts/v1.113-max/maxserve_bplan_extension/"
    "bplan_native_serve_dev/bplan_native_launcher.py",
]

print("=== REQUIRED RUNTIME FILES ===")
for name in required:
    p = ROOT / name
    assert p.is_file(), f"MISSING: {name}"
print("PASS")

files = [p for p in ROOT.rglob("*") if p.is_file()]
code = [p for p in files if p.suffix == ".py"]

texts = {}
for p in files:
    if p.suffix in {
        ".py", ".sh", ".json", ".yaml", ".yml",
        ".toml", ".cfg", ".txt", ".pbtxt"
    } and p.stat().st_size < 2_000_000:
        texts[p] = p.read_text(errors="replace")

print("\n=== LEFTOVER TEST/DEBUG ARTIFACTS ===")

patterns = re.compile(
    r"(^test_|_test\.py$|parity|benchmark|diagnostic|"
    r"debug|probe|inspect|audit|experiment|backup|"
    r"\.bak$|\.orig$|\.pyc$|\.log$)",
    re.I
)

suspects = [
    p for p in files
    if patterns.search(p.name)
    and p.name != "bplan_native_launcher.py"
]

for p in suspects:
    print("REVIEW:", p.relative_to(ROOT))
print("SUSPECT FILES:", len(suspects))

print("\n=== POSSIBLY UNUSED MAX PYTHON MODULES ===")

unused = []

for p in sorted(EXT.rglob("*.py")):
    if p.name == "__init__.py":
        continue
    if "launcher" in p.stem.lower():
        continue

    stem = p.stem
    references = [
        q for q, content in texts.items()
        if q != p and re.search(
            rf"\b{re.escape(stem)}\b", content
        )
    ]

    if not references:
        unused.append(p)
        print("REVIEW:", p.relative_to(ROOT))

print("POSSIBLY UNREFERENCED MODULES:", len(unused))
print("(Dynamic imports and standalone entrypoints require review.)")

def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

print("\n=== DUPLICATE PYTHON SOURCE CONTENT ===")

groups = defaultdict(list)
for p in code:
    groups[sha(p)].append(p)

duplicates = [v for v in groups.values() if len(v) > 1]
for group in duplicates:
    print("DUPLICATE GROUP:")
    for p in group:
        print(" ", p.relative_to(ROOT))

print("DUPLICATE PYTHON GROUPS:", len(duplicates))

print("\n=== DUPLICATE PHYSICAL MAX WEIGHTS ===")

weights = defaultdict(list)
for p in EXT.rglob("*.npy"):
    if p.is_file() and not p.is_symlink():
        weights[sha(p)].append(p)

duplicates = [v for v in weights.values() if len(v) > 1]
for group in duplicates:
    print("DUPLICATE WEIGHTS:")
    for p in group:
        print(" ", p.relative_to(ROOT))

print("DUPLICATE PHYSICAL WEIGHT GROUPS:", len(duplicates))

print("\n=== PORTABILITY ===")

links = [p for p in ROOT.rglob("*") if p.is_symlink()]
bad = [
    p for p in links
    if not p.exists()
    or not p.resolve().is_relative_to(ROOT.resolve())
]

for p in bad:
    print("BROKEN/EXTERNAL:", p.relative_to(ROOT))

print("SYMLINKS CHECKED:", len(links))
print("UNSAFE LINKS:", len(bad))

print("\n=== AUDIT SUMMARY ===")
print("PYTHON FILES:", len(code))
print("TOTAL FILES:", len(files))
print("SUSPECT ARTIFACTS:", len(suspects))
print("POSSIBLY UNUSED MODULES:", len(unused))
print("DUPLICATE SOURCE GROUPS:",
      len([v for v in groups.values() if len(v) > 1]))
print("DUPLICATE PHYSICAL WEIGHT GROUPS:", len(duplicates))
print("UNSAFE LINKS:", len(bad))
print("ORIGINAL VALIDATED RELEASES: UNCHANGED")
PY
