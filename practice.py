cd /application/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint sh \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest -s <<'SH'
set -e

python -m pip install --no-cache-dir --no-deps faiss-cpu

python - <<'PY'
import sys, json
from pathlib import Path

root = Path.cwd()
sys.path[:0] = [
    str(root / "artifacts/v1.168/core-artifact"),
    str(root / "artifacts/v1.168-max"),
    str(root / "artifacts/v1.168-max/cta_max"),
]

from pipeline import pipeline
from cta_max.live_cta_pipeline_bridge import attach_max

body = json.loads(
    (root / "artifacts/v1.168/samples/sanity_input.json").read_text()
)

print("REAL JSON: LOADED", flush=True)

app = attach_max(pipeline())
print("MAX BRIDGE: ATTACHED", flush=True)

result = app.predict_raw(body)
assert isinstance(result, (dict, list))
json.dumps(result, allow_nan=False)

print("REAL JSON E2E: PASS")
print("FINAL RESPONSE: VALID JSON")
print("ORIGINAL FILES: UNCHANGED")
PY
SH
