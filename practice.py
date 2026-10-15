python3 - <<'PY'
from pathlib import Path
from collections import defaultdict
import hashlib

root = Path("artifacts/v1.168-max")
groups = defaultdict(list)

for p in root.rglob("*"):
    if p.is_file() and p.suffix in (".npy", ".npz", ".pt"):
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        groups[digest].append(p)

duplicates = [v for v in groups.values() if len(v) > 1]

print("DUPLICATE WEIGHT GROUPS:", len(duplicates))
for group in duplicates[:10]:
    print("\nEXACT DUPLICATES:")
    for p in group:
        print(" ", p)

print("\nNO FILES CHANGED OR DELETED")
PY
