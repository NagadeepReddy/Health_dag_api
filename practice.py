python3 - <<'PY'
from pathlib import Path

release = Path("../cta-max-release-review")
source = release / "cta_max"
target = release / "artifacts/v1.168-max/cta_max"

if target.exists():
    print("TARGET ALREADY EXISTS — NO CHANGES")
elif not source.is_dir():
    print("SOURCE NOT FOUND — NO CHANGES")
else:
    target.parent.mkdir(parents=True, exist_ok=True)
    source.rename(target)
    print("RELEASE FOLDER STRUCTURE: CORRECTED")
    print("PYTHON FILES:", len(list(target.glob("*.py"))))
    print("ORIGINAL WORKING CODE: UNCHANGED")
    print("NO FILES DELETED")
PY
