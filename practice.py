python3 - <<'PY'
from pathlib import Path
import shutil

root = Path("artifacts/v1.168-max")
destination = Path("../cta-max-release-review/cta_max")

files = [
    Path(line.strip())
    for line in (root / "RELEASE_CANDIDATE.txt").read_text().splitlines()
    if line.strip() and not line.startswith("#")
]
files.append(root / "cta_max/__init__.py")

if destination.parent.exists():
    print("REVIEW FOLDER ALREADY EXISTS — NO CHANGES")
elif any(not p.is_file() for p in files):
    print("MISSING FILES — NO CHANGES")
else:
    destination.mkdir(parents=True)
    for p in files:
        shutil.copy2(p, destination / p.name)

    print("CLEAN MAX SOURCE PACKAGE: READY")
    print("FILES COPIED:", len(files))
    print("ORIGINAL FILES: UNCHANGED")
    print("MODEL WEIGHTS: UNCHANGED")
    print("NOT COMMITTED OR PUSHED")
PY
