cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
python3 -B -S - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_spawn_worker.py")
old = "faulthandler.dump_traceback_later(3, repeat=False)"

s = p.read_text()

if s.count(old) != 1:
    raise SystemExit("STOP: expected diagnostic timer not found exactly once")

updated = s.replace(old, "# Disabled 3-second diagnostic traceback timer", 1)
compile(updated, str(p), "exec")

p.write_text(updated)

print("CTA 3-SECOND DIAGNOSTIC TIMER: DISABLED")
print("PYTHON SYNTAX: PASS")
print("ORIGINAL MAX FILES: UNCHANGED")
print("DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
