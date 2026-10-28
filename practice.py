cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
python3 -B -S - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_worker_adapter.py")
s = p.read_text()

old = "            pipeline.load()"
new = """            import time
            started = time.monotonic()
            print("CTA MODEL LOAD: START", flush=True)
            try:
                pipeline.load()
            finally:
                print(f"CTA MODEL LOAD: ELAPSED {time.monotonic() - started:.1f}s", flush=True)"""

if s.count(old) != 1:
    raise SystemExit("STOP: expected load statement not found exactly once")

updated = s.replace(old, new, 1)
compile(updated, str(p), "exec")
p.write_text(updated)
print("CTA LOAD TIMING: INSTALLED")
print("PYTHON SYNTAX: PASS")
print("DS CODE: UNCHANGED")
PY
