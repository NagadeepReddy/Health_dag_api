podman run --rm -i --pull=never \
  -v "$PWD:/work:ro" -w /work \
  --entrypoint python3 cta-max-faiss:local - <<'PY'
import sys, json
from pathlib import Path

sys.dont_write_bytecode = True
sys.path[:0] = [
    "/work/artifacts/v1.168/core-artifact",
    "/work/artifacts/v1.168-max",
    "/work/artifacts/v1.168-max/cta_max",
]

from pipeline import pipeline as CTA
from cta_max.live_cta_pipeline_bridge import attach_max

p = CTA()
p.load()
attach_max(p)

sample = Path("artifacts/v1.168/samples/sanity_input.json")
body = json.loads(sample.read_text())

print("RUNNING FULL CTA JSON...", flush=True)
result = p.predict_raw(body)

print("FINAL RESPONSE TYPE:", type(result).__name__)
print("FINAL RESPONSE:", json.dumps(result, default=str)[:2000])
print("CTA JSON E2E: PASS")
PY
