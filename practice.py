cd /application1/sajjna8/rt-pzaas-cta-offers-v1

cat > artifacts/v1.168-max/maxserve_cta_extension/cta_native_startup_test.py <<'PY'
from types import SimpleNamespace
from fastapi.testclient import TestClient
from max.serve import api_server
from max.serve.config import Settings, APIType
from maxserve_cta_extension.cta_spawn_worker import (
    CTAFactoryWrapper,
    install_cta_spawn_entry,
)
from maxserve_cta_extension.cta_router import register_cta_routes
from maxserve_cta_extension.cta_http_pipeline import CTANativeHTTPPipeline


def unused_factory():
    raise RuntimeError("CTA factory wrapper was not invoked")


def main():
    install_cta_spawn_entry()
    register_cta_routes()
    api_server.TokenGeneratorPipeline = CTANativeHTTPPipeline

    config = SimpleNamespace(
        model_config=SimpleNamespace(model_name="cta"),
        zmq_endpoint_base="ipc:///tmp/cta-max-native",
        lora_config=None,
    )

    serving = api_server.ServingTokenGeneratorSettings(
        model_factory=CTAFactoryWrapper(unused_factory),
        pipeline_config=config,
        tokenizer=None,
    )

    app = api_server.fastapi_app(
        Settings(
            api_types=[APIType.KSERVE],
            disable_telemetry=True,
        ),
        serving,
    )

    assert "/v2/cta/predict" in [r.path for r in app.routes]
    print("CTA ROUTES: PASS", flush=True)
    print("STARTING NATIVE MAX WORKER...", flush=True)

    with TestClient(app) as client:
        print("MAX NATIVE WORKER STARTUP: PASS", flush=True)
        response = client.post("/v2/cta/probe")
        print("CTA PROBE:", response.status_code, response.text, flush=True)


if __name__ == "__main__":
    main()
PY

python3 -m py_compile \
  artifacts/v1.168-max/maxserve_cta_extension/cta_native_startup_test.py || exit 1

timeout 90s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  -v "$PWD:/workspace:Z" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -u /workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_startup_test.py

echo "STARTUP EXIT CODE: $?"
