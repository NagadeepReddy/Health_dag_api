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

files += [
    str(root / "cta_max/__init__.py"),
    str(root / ".gitignore"),
]

files = sorted(set(files))

if len(files) != 18 or any(not Path(f).is_file() for f in files):
    print("FILE VALIDATION FAILED — NOTHING STAGED")
else:
    subprocess.run(["git", "add", "--", *files], check=True)
    print("STAGED FILES:")
    subprocess.run(["git", "diff", "--cached", "--name-only"], check=True)
    subprocess.run(["git", "diff", "--cached", "--check"], check=True)
    print("MAX SOURCE STAGING COMPLETE")
    print("NOT COMMITTED OR PUSHED")
PY
