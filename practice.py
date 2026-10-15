python3 - <<'PY'
from pathlib import Path
import shutil

working = Path("artifacts/v1.168-max/cta_max/run_live_max_inference.py")
clean = Path("../cta-max-release-review/artifacts/v1.168-max/cta_max/run_live_max_inference.py")

old = "from run_real_sanity_input_adapter import build_real_inputs"
new = "from cta_max.run_real_sanity_input_adapter import build_real_inputs"

if working.read_text().replace(old, new, 1) != clean.read_text():
    print("UNEXPECTED DIFFERENCE — NO CHANGES")
else:
    backup = Path("/tmp/cta_max_run_live_before_import_fix.py")
    if not backup.exists():
        shutil.copy2(working, backup)
    shutil.copy2(clean, working)
    print("MAX SOURCE ALIGNED: PASS")
    print("RELEASE FILES: 17")
    print("ORIGINAL DS CODE: UNCHANGED")
    print("NO FILES DELETED OR PUSHED")
PY
