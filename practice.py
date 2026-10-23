cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --memory=8g \
  -p 127.0.0.1:18080:8000 \
  -v "$PWD:/workspace:ro" \
  -w /workspace \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PY'
from types import SimpleNamespace
import uvicorn
from max.serve import api_server
from max.serve.config import Settings
from max.interfaces import PipelineTask
from maxserve_cta_extension.cta_spawn_worker import (
    CTAFactoryWrapper, install_cta_spawn_entry
)
from maxserve_cta_extension.cta_router import register_cta_routes

def real_cta_factory():
    from pipeline import pipeline as CTA
    return CTA()

install_cta_spawn_entry()
register_cta_routes()

config = SimpleNamespace(
    model_config=SimpleNamespace(
        model_name="cta-offers-v1.168",
        model_path="/workspace/artifacts/v1.168/core-artifact"
    ),
    lora_config=None,
    zmq_endpoint_base="ipc:///tmp/cta-max-native"
)

serving = api_server.ServingTokenGeneratorSettings(
    model_factory=CTAFactoryWrapper(real_cta_factory),
    pipeline_config=config,
    tokenizer=None,
    pipeline_task=PipelineTask.TEXT_GENERATION
)

app = api_server.fastapi_app(
    Settings(api_types=[api_server.APIType.KSERVE]),
    serving
)

print("CTA NATIVE HTTP STARTING", flush=True)
uvicorn.run(app, host="0.0.0.0", port=8000)
PY
