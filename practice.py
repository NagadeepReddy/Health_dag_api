python3 - <<'PY'
from pathlib import Path
import hashlib

working = Path("artifacts/v1.168-max/cta_max")
clean = Path("../cta-max-release-review/artifacts/v1.168-max/cta_max")

files = sorted(clean.glob("*.py"))
print("CLEAN RELEASE FILES:", len(files))
print("\nDIFFERENCES FROM WORKING CODE:")

count = 0
for p in files:
    original = working / p.name
    if not original.exists():
        print("MISSING IN WORKING:", p.name)
        count += 1
    elif hashlib.sha256(p.read_bytes()).digest() != hashlib.sha256(original.read_bytes()).digest():
        print("DIFFERENT:", p.name)
        count += 1

print("\nTOTAL DIFFERENCES:", count)
print("NO FILES MODIFIED OR DELETED")
PY
