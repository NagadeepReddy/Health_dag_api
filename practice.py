python3 - <<'PY'
from pathlib import Path

p = Path("../cta-max-release-review/artifacts/v1.168-max/cta_max/run_live_max_inference.py")

old = "from run_real_sanity_input_adapter import build_real_inputs"
new = "from cta_max.run_real_sanity_input_adapter import build_real_inputs"

text = p.read_text()

if old in text:
    p.write_text(text.replace(old, new, 1))
    print("CLEAN RELEASE IMPORT: FIXED")
elif new in text:
    print("IMPORT ALREADY CORRECT")
else:
    print("EXPECTED IMPORT NOT FOUND — NO CHANGES")

print("ORIGINAL WORKING CODE: UNCHANGED")
print("ORIGINAL DS CODE: UNCHANGED")
PY
