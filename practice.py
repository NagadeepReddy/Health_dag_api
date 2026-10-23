cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  -v "$PWD:/workspace:ro" \
  -w /workspace \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local - <<'PY'
from types import SimpleNamespace
from max.serve import api_server
from max.serve.config import Settings
from max.interfaces import PipelineTask
from maxserve_cta_extension.cta_spawn_worker import CTAFactoryWrapper
from maxserve_cta_extension.cta_router import register_cta_routes

def real_cta_factory():
    from pipeline import pipeline
    return pipeline()

config = SimpleNamespace(
    model_config=SimpleNamespace(
        model_name="cta-offers-v1.168",
        model_path="/workspace/artifacts/v1.168/core-artifact"
    ),
    lora_config=None,
    zmq_endpoint_base="ipc:///tmp/cta-max-native"
)

register_cta_routes()

serving = api_server.ServingTokenGeneratorSettings(
    model_factory=CTAFactoryWrapper(real_cta_factory),
    pipeline_config=config,
    tokenizer=None,
    pipeline_task=PipelineTask.TEXT_GENERATION
)

app = api_server.fastapi_app(Settings(), serving)
print("NATIVE MAX APP: PASS")
print("CTA PREDICT ROUTE:", any(
    r.path == "/v2/cta/predict" for r in app.routes
))
PY
