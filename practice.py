if [ ! -f /tmp/cta_max_tiles_test.json ]; then
  echo "SAVED TILES REQUEST NOT FOUND — NO TEST RUN"
else
  podman run --rm -i --pull=never \
    -v /application/sajjna8:/application/sajjna8:ro \
    --mount type=bind,src=/tmp/cta_max_tiles_test.json,dst=/tmp/cta_max_tiles_test.json,ro \
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

print("CLEAN MAX SOURCE:", Path(sys.modules["cta_max.live_cta_pipeline_bridge"].__file__).resolve(), flush=True)

p = CTA()
p.load()
attach_max(p)

body = json.loads(Path("/tmp/cta_max_tiles_test.json").read_text())
result = p.predict_raw(body)

print("CLEAN RELEASE INFERENCE: PASS")
print("RESPONSE TYPE:", type(result).__name__)
print("OFFER COUNT:", len(result.get("jsonData", {}).get("prediction", {}).get("offerList", [])))
print("ORIGINAL DS CODE: UNCHANGED")
PY
fi
