python3 - <<'PY'
from pathlib import Path
from collections import defaultdict
import hashlib

root = Path("../cta-max-release-review/artifacts/v1.168-max/cta_max")
files = sorted(root.glob("*.py"))

print("RELEASE DIRECTORY EXISTS:", root.is_dir())
print("PYTHON FILES:", len(files))

groups = defaultdict(list)
for p in files:
    digest = hashlib.sha256(p.read_bytes()).hexdigest()
    groups[digest].append(p.name)

duplicates = [names for names in groups.values() if len(names) > 1]

print("EXACT DUPLICATES:", len(duplicates))
for names in duplicates:
    print("DUPLICATE:", names)

print("NO FILES MODIFIED OR DELETED")
PY
