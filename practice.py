python3 - <<'PY'
import subprocess
from pathlib import Path

files = subprocess.check_output(
    ["git", "ls-files", "--others", "--exclude-standard",
     "artifacts/v1.168-max"],
    text=True
).splitlines()

for label, selected in [
    ("PYTHON FILES", [f for f in files if f.endswith(".py")]),
    ("MODEL WEIGHTS", [f for f in files if f.endswith((".npy", ".npz", ".pt"))]),
    ("OTHER FILES", [f for f in files if not f.endswith((".py", ".npy", ".npz", ".pt"))])
]:
    print(f"\n{label}: {len(selected)}")
    for f in selected[:12]:
        print(" ", f)
    if len(selected) > 12:
        print(f"  ... and {len(selected)-12} more")

print("\nNO FILES MODIFIED OR STAGED")
PY
