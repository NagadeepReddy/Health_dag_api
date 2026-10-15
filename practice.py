python3 - <<'PY'
from pathlib import Path
import subprocess

root = Path("artifacts/v1.168-max")
manifest = root / "RELEASE_CANDIDATE.txt"

files = [
    line.strip()
    for line in manifest.read_text().splitlines()
    if line.strip() and not line.startswith("#")
]

files.append(str(root / ".gitignore"))

if not all(Path(f).is_file() for f in files):
    print("MISSING FILES — STOP")
else:
    print("FILES SELECTED:", len(files))
    print("GIT DRY RUN:")
    subprocess.run(["git", "add", "--dry-run", "--", *files], check=True)
    print("NOTHING STAGED OR COMMITTED")
PY
