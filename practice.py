cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

cat > artifacts/v1.168-max/maxserve_cta_extension/cta_spawn_safe_probe.py <<'PY'
import json
from pathlib import Path

import uvicorn
from fastapi.testclient import TestClient


def main():
    from maxserve_cta_extension import cta_native_http_entry as entry

    original_settings = entry.Settings

    def settings_without_telemetry(*args, **kwargs):
        kwargs["disable_telemetry"] = True
        return original_settings(*args, **kwargs)

    entry.Settings = settings_without_telemetry

    def test_once(app, *args, **kwargs):
        sample = Path(
            "/workspace/artifacts/v1.168/samples/sanity_input.json"
        )
        if not sample.is_file():
            raise RuntimeError("Real CTA sample missing")

        with TestClient(app) as client:
            print("NATIVE MAX STARTUP: PASS", flush=True)

            probe = client.post("/v2/cta/probe")
            print("PROBE:", probe.status_code, flush=True)

            if probe.status_code != 200:
                raise RuntimeError("CTA probe failed")

            body = json.loads(sample.read_text())
            response = client.post("/v2/cta/predict", json=body)

            print("CTA STATUS:", response.status_code, flush=True)
            print("CTA RESPONSE:", response.text[:1200], flush=True)

            if response.status_code != 200:
                raise RuntimeError("Native CTA inference failed")

            print("NATIVE CTA JSON E2E: PASS", flush=True)

    uvicorn.run = test_once
    entry.main()


if __name__ == "__main__":
    main()
PY

timeout -k 5s 75s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
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
  localhost/cta-max-faiss:local \
  /workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_spawn_safe_probe.py
