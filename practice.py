cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
python3 -B -S - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_spawn_worker.py")
s = p.read_text()

old = "# Disabled 3-second diagnostic traceback timer"
new = "faulthandler.dump_traceback_later(20, repeat=False)"

if s.count(old) != 1:
    raise SystemExit("STOP: expected diagnostic marker not found exactly once")

updated = s.replace(old, new, 1)
compile(updated, str(p), "exec")
p.write_text(updated)

print("CTA 20-SECOND DIAGNOSTIC: INSTALLED")
print("PYTHON SYNTAX: PASS")
print("DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
