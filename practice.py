sample=/tmp/cta_max_tiles_postman.json
[ -f "$sample" ] || sample=/tmp/cta_max_tiles_test.json

podman run --rm -i --pull=never \
  -e modelId=rt-pzaas-cta-offers-v1 \
  -e expThrottleLabel=T \
  -v /application/sajjna8:/application/sajjna8:ro \
  -v "$sample:/request.json:ro" \
  -w /application/sajjna8/cta-max-release-review \
  --entrypoint python3 cta-max-faiss:local - <<'PY'
import sys, json
from pathlib import Path

sys.dont_write_bytecode = True
sys.path[:0] = [
    str(Path.cwd() / "artifacts/v1.168/core-artifact"),
    str(Path.cwd() / "artifacts/v1.168-max"),
]

from pipeline import pipeline as CTA
from cta_max.live_cta_pipeline_bridge import attach_max

p = CTA()
p.load()
attach_max(p)

result = p.predict_raw(json.loads(Path("/request.json").read_text()))

print("CLEAN RELEASE E2E: PASS")
print("FINAL RESPONSE:", json.dumps(result, default=str)[:1500])
PY
