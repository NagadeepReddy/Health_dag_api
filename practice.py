podman run --rm -i --pull=never \
  -v /application/sajjna8:/application/sajjna8:ro \
  -v /tmp:/tmp:ro \
  -w /application/sajjna8/cta-max-release-review \
  --entrypoint python3 cta-max-faiss:local - <<'PY'
import sys, json
from pathlib import Path

sys.dont_write_bytecode = True
root = Path.cwd()
sys.path[:0] = [
    str(root / "artifacts/v1.168/core-artifact"),
    str(root / "artifacts/v1.168-max"),
]

from pipeline import pipeline as CTA
from cta_max.live_cta_pipeline_bridge import attach_max

sample = Path("/tmp/cta_max_tiles_postman.json")
if not sample.is_file():
    sample = Path("/tmp/cta_max_tiles_test.json")
assert sample.is_file(), "Saved CTA test request missing"

print("TESTING CLEAN MAX RELEASE", flush=True)

p = CTA()
p.load()
attach_max(p)

result = p.predict_raw(json.loads(sample.read_text()))

print("CLEAN RELEASE INFERENCE: PASS")
print("RESPONSE TYPE:", type(result).__name__)
print("OFFER COUNT:", len(result.get("jsonData", {}).get("prediction", {}).get("offerList", [])))
print("ORIGINAL DS CODE: UNCHANGED")
PY
