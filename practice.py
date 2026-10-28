cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
python3 -B -S - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_worker_adapter.py")
s = p.read_text()

old = 'print("CTA PREDICT_RAW: START", flush=True)'
new = '''print("CTA PREDICT_RAW: START", flush=True)
        import faulthandler
        faulthandler.dump_traceback_later(20, repeat=False)'''

if s.count(old) != 1:
    raise SystemExit("STOP: prediction entry not found exactly once")

if "faulthandler.dump_traceback_later" in s:
    raise SystemExit("STOP: diagnostic already configured in adapter")

updated = s.replace(old, new, 1)
compile(updated, str(p), "exec")
p.write_text(updated)

print("CTA PREDICTION DIAGNOSTIC: INSTALLED")
print("TIMER: RESTARTS WHEN PREDICTION BEGINS")
print("PYTHON SYNTAX: PASS")
print("DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
