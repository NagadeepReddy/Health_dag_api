cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
timeout -k 5s 75s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run -i --rm --pull=never \
  --memory=2g --cpus=2 --pids-limit=128 \
  --network=none --read-only --log-driver=none \
  --tmpfs /tmp:rw,size=256m,mode=1777 \
  --tmpfs /opt/venv/lib/python3.12/site-packages/max/_core_mojo/__mojocache__:rw,size=64m,mode=1777 \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e PYTHONPATH=/workspace:/workspace/artifacts/v1.168-max \
  -e OMP_NUM_THREADS=1 \
  -e OPENBLAS_NUM_THREADS=1 \
  -e MKL_NUM_THREADS=1 \
  -e TOKENIZERS_PARALLELISM=false \
  -v "$PWD":/workspace:ro \
  -w /workspace \
  --entrypoint /opt/venv/bin/python3 \
  localhost/cta-max-faiss:local - <<'PY'
import json
import runpy
from pathlib import Path
import uvicorn
from fastapi.testclient import TestClient

samples = sorted(Path("/workspace/artifacts").glob("v*/samples/sanity_input.json"))
if not samples:
    raise SystemExit("STOP: Real CTA sanity_input.json not found")

sample = samples[-1]
print("REAL CTA SAMPLE:", sample, flush=True)

def test_once(app, *args, **kwargs):
    with TestClient(app) as client:
        probe = client.post("/v2/cta/probe")
        print("CTA PROBE:", probe.status_code, probe.text[:300], flush=True)
        if probe.status_code != 200:
            raise SystemExit("STOP: CTA probe failed")

        body = json.loads(sample.read_text())
        print("SENDING REAL CTA JSON", flush=True)
        result = client.post("/v2/cta/predict", json=body)
        print("NATIVE CTA STATUS:", result.status_code, flush=True)
        print("NATIVE CTA RESPONSE:", result.text[:1200], flush=True)

uvicorn.run = test_once
runpy.run_module(
    "maxserve_cta_extension.cta_native_http_entry",
    run_name="__main__"
)
PY
