cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
python3 -B -S - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/cta_max/run_live_max_inference.py")
s = p.read_text()

old = "infer_max_live.max_model = model"
new = "infer_max_live._max_model = model"

if s.count(old) != 1:
    raise SystemExit("STOP: expected cache assignment not found exactly once")

if 'getattr(infer_max_live, "_max_model", None)' not in s:
    raise SystemExit("STOP: cache reader does not match")

updated = s.replace(old, new, 1)
compile(updated, str(p), "exec")

backup = p.with_suffix(".py.pre_cache_fix.bak")
if backup.exists():
    raise SystemExit("STOP: backup already exists")

backup.write_bytes(p.read_bytes())
p.write_text(updated)

print("MAX MODEL CACHE FIX: PASS")
print("BACKUP:", backup)
print("PYTHON SYNTAX: PASS")
print("DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
