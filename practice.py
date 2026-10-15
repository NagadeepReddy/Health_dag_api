python3 - <<'PY'
from pathlib import Path
from collections import defaultdict

root = Path("artifacts/v1.168-max")
groups = defaultdict(lambda: [0, 0])

for p in root.rglob("*"):
    if p.is_file() and p.suffix in (".npy", ".npz", ".pt"):
        groups[str(p.parent)][0] += 1
        groups[str(p.parent)][1] += p.stat().st_size

for folder, (count, size) in sorted(groups.items()):
    print(f"{count:4} files | {size/1048576:7.1f} MB | {folder}")

print("NO FILES CHANGED")
PY
