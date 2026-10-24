cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  -v "$PWD:/workspace:Z" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PY'
from types import SimpleNamespace
from max.serve import api_server
from max.serve.config import Settings
from maxserve_cta_extension.cta_spawn_worker import (
    CTAFactoryWrapper,
    install_cta_spawn_entry,
)
from maxserve_cta_extension.cta_router import register_cta_routes
from maxserve_cta_extension.cta_http_pipeline import CTANativeHTTPPipeline

class UnusedFactory:
    def __call__(self):
        raise RuntimeError("CTA factory wrapper was not used")

install_cta_spawn_entry()
register_cta_routes()
api_server.TokenGeneratorPipeline = CTANativeHTTPPipeline

config = SimpleNamespace(
    model_config=SimpleNamespace(model_name="cta"),
    zmq_endpoint_base="ipc:///tmp/cta-max-native",
    lora_config=None,
)

serving = api_server.ServingTokenGeneratorSettings(
    model_factory=CTAFactoryWrapper(UnusedFactory()),
    pipeline_config=config,
    tokenizer=None,
)

app = api_server.fastapi_app(Settings(), serving)

paths = [r.path for r in app.routes]
print("MAX BUILT-IN APP: CREATED")
print("CTA ROUTES:", [p for p in paths if "/cta/" in p])
print("CTA ROUTE CHECK:", "PASS" if "/cta/predict" in paths else "FAIL")
PY
