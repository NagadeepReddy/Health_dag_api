cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
python3 -B -S - <<'PY'
from pathlib import Path
import re

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_native_e2e_test.py")
sample = Path("artifacts/v1.168-max/cta_native_adjusted_sanity_input.json")
new_path = "/workspace/artifacts/v1.168-max/cta_native_adjusted_sanity_input.json"

if not sample.is_file():
    raise SystemExit("STOP: adjusted JSON missing")

s = p.read_text()
pattern = re.compile(
    r"""(\bsample\s*=\s*Path\s*\(\s*)(['"])([^'"\r\n]*sanity_input\.json)\2(\s*\))"""
)
matches = list(pattern.finditer(s))

if len(matches) != 1:
    raise SystemExit(f"STOP: expected one sample assignment, found {len(matches)}")

m = matches[0]
old_path = m.group(3)

if old_path == new_path:
    print("NATIVE TEST INPUT: ALREADY UPDATED")
else:
    updated = s[:m.start(3)] + new_path + s[m.end(3):]
    compile(updated, str(p), "exec")
    p.write_text(updated)
    print("NATIVE TEST INPUT: UPDATED")

print("PYTHON SYNTAX: PASS")
print("ORIGINAL JSON: UNCHANGED")
print("DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
