cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
python3 -B -S - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_worker_adapter.py")
s = p.read_text()

old = """        try:
            return pipeline.predict_raw(body)
        finally:
            print(f"CTA PREDICT_RAW: ELAPSED {time.monotonic()-started:.1f}s", flush=True)"""

new = """        try:
            return pipeline.predict_raw(body)
        except Exception as exc:
            import traceback
            print(f"CTA PREDICT_RAW EXCEPTION: {type(exc).__name__}: {exc}", flush=True)
            traceback.print_exc()
            raise
        finally:
            print(f"CTA PREDICT_RAW: ELAPSED {time.monotonic()-started:.1f}s", flush=True)"""

if s.count(old) != 1:
    raise SystemExit("STOP: expected timing block not found; no changes made")

updated = s.replace(old, new, 1)
compile(updated, str(p), "exec")
p.write_text(updated)

print("CTA EXCEPTION LOGGING: INSTALLED")
print("PYTHON SYNTAX: PASS")
print("DS CODE: UNCHANGED")
PY
