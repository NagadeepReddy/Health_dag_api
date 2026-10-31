python3 -B - <<'PY'
from pathlib import Path
from collections import defaultdict
import hashlib

root = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max/cta_native_batch2_release_candidate")
files = sorted(p for p in root.rglob("*") if p.is_file())

print("=== COMPLETE FILE INVENTORY ===")
for p in files:
    print(f"{p.relative_to(root)} | {p.stat().st_size} bytes")

print("\n=== IDENTICAL FILE CONTENT ===")
groups = defaultdict(list)
for p in files:
    if p.stat().st_size <= 10_000_000:
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        groups[digest].append(str(p.relative_to(root)))

duplicates = [names for names in groups.values() if len(names) > 1]
if duplicates:
    for names in duplicates:
        print("DUPLICATE:", " | ".join(names))
else:
    print("No identical files found among scanned files")

print("\nTOTAL FILES:", len(files))
print("ACCEPTANCE REPORT EXISTS:", (root / "CTA_NATIVE_BATCH2_CPU_ACCEPTANCE_20261030.json").is_file())
PY
