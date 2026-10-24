cd /application1/sajjna8/rt-pzaas-cta-offers-v1

timeout 60s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  -v "$PWD:/workspace:Z" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PY'
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

install_cta_spawn_entry()
register_cta_routes()
api_server.TokenGeneratorPipeline = CTANativeHTTPPipeline

config = SimpleNamespace(
    model_config=SimpleNamespace(model_name="cta"),
    zmq_endpoint_base="ipc:///tmp/cta-max-native",
    lora_config=None,
)

serving = api_server.ServingTokenGeneratorSettings(
    model_factory=CTAFactoryWrapper(lambda: None),
    pipeline_config=config,
    tokenizer=None,
)

app = api_server.fastapi_app(
    Settings(api_types=[APIType.KSERVE]),
    serving,
)

print("CTA ROUTES: PASS", flush=True)
print("STARTING MAX NATIVE LIFECYCLE...", flush=True)

try:
    with TestClient(app) as client:
        print("MAX NATIVE LIFECYCLE: PASS", flush=True)
        response = client.post("/v2/cta/probe")
        print("CTA PROBE:", response.status_code, response.text, flush=True)
except Exception:
    import traceback
    print("MAX NATIVE LIFECYCLE: BLOCKED", flush=True)
    traceback.print_exc(limit=8)
PY
