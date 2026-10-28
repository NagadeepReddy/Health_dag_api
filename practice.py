cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
python3 -B -S - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_worker_adapter.py")
s = p.read_text()

old = "return self.initialize().predict_raw(body)"

new = """pipeline = self.initialize()
        import time

        for stage in ("preprocess", "postprocess"):
            original = getattr(pipeline, stage, None)
            if callable(original) and not getattr(original, "_cta_timed", False):
                def timed(*args, _fn=original, _stage=stage, **kwargs):
                    started = time.monotonic()
                    print(f"CTA {_stage}: START", flush=True)
                    try:
                        return _fn(*args, **kwargs)
                    finally:
                        print(f"CTA {_stage}: ELAPSED {time.monotonic()-started:.1f}s", flush=True)
                timed._cta_timed = True
                setattr(pipeline, stage, timed)

        started = time.monotonic()
        print("CTA PREDICT_RAW: START", flush=True)
        try:
            return pipeline.predict_raw(body)
        finally:
            print(f"CTA PREDICT_RAW: ELAPSED {time.monotonic()-started:.1f}s", flush=True)"""

if s.count(old) != 1:
    raise SystemExit("STOP: prediction statement does not match; no changes made")

updated = s.replace(old, new, 1)
compile(updated, str(p), "exec")
p.write_text(updated)

print("CTA PREDICTION TIMING: INSTALLED")
print("PYTHON SYNTAX: PASS")
print("DS CODE: UNCHANGED")
PY
