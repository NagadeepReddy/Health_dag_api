python3 - <<'PY'
from pathlib import Path
from collections import defaultdict
import hashlib

root = Path("../cta-max-release-review/cta_max")
groups = defaultdict(list)
files = sorted(root.glob("*.py"))

for p in files:
    digest = hashlib.sha256(p.read_bytes()).hexdigest()
    groups[digest].append(p.name)

print("RELEASE PYTHON FILES:", len(files))
print("\nEXACT DUPLICATES:")
duplicates = [v for v in groups.values() if len(v) > 1]
if duplicates:
    for group in duplicates:
        print(group)
else:
    print("NONE")

print("\nNO FILES CHANGED OR DELETED")
PY
