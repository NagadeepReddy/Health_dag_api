python3 - <<'PY'
from pathlib import Path
import re

root = Path("artifacts/v1.168-max")
runtime = [
    Path(line.strip())
    for line in (root / "RELEASE_CANDIDATE.txt").read_text().splitlines()
    if line.strip() and not line.startswith("#")
]

source = "\n".join(p.read_text() for p in runtime)
other = sorted(
    p for p in (root / "cta_max").glob("*.py")
    if p not in runtime
)

print("ADDITIONAL FILES REFERENCED BY RUNTIME:")
found = 0
for p in other:
    if p.name == "__init__.py":
        continue
    if re.search(r"\b" + re.escape(p.stem) + r"\b", source):
        print(p.name)
        found += 1

print("REFERENCED FILES:", found)
print("NO FILES MODIFIED OR DELETED")
PY
