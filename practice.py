python3 - <<'PY'
from pathlib import Path

root = Path("artifacts/v1.168-max")

files = sorted(
    p for p in root.rglob("README.md")
    if p.is_file()
)

print("README FILES FOUND:", len(files))

for p in files:
    print("\nFILE:", p)
    print("SIZE:", p.stat().st_size, "bytes")
    print("CONTENT PREVIEW:")
    for line in p.read_text(errors="replace").splitlines()[:25]:
        print(line)

print("\nNO FILES CHANGED OR DELETED")
PY
