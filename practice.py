cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
python3 -B -S - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_native_e2e_test.py")

old = "/workspace/artifacts/v1.168/samples/sanity_input.json"
new = "/workspace/artifacts/v1.168-max/cta_native_adjusted_sanity_input.json"

sample = Path("artifacts/v1.168-max/cta_native_adjusted_sanity_input.json")

if not sample.is_file():
    raise SystemExit("STOP: adjusted JSON missing")

s = p.read_text()

if s.count(old) != 1:
    raise SystemExit("STOP: expected original test path not found exactly once")

updated = s.replace(old, new, 1)
compile(updated, str(p), "exec")
p.write_text(updated)

print("NATIVE MAX TEST INPUT: UPDATED")
print("ADJUSTED JSON: SELECTED")
print("PYTHON SYNTAX: PASS")
print("ORIGINAL JSON: UNCHANGED")
print("DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
