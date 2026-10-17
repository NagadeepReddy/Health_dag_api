
podman run --rm -i --entrypoint /bin/bash \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  -lc '/opt/venv/bin/python -' <<'PY'
from max.serve.api_server import (
    fastapi_app, Settings,
    ServingTokenGeneratorSettings, ROUTES
)
from max.serve.config import APIType
from max.pipelines import PipelineConfig

async def cta_probe():
    return {"status": "ok"}

ROUTES[APIType.KSERVE].router.add_api_route(
    "/cta/probe", cta_probe, methods=["POST"]
)

config = PipelineConfig()
print("ZMQ CONFIG:", config.zmq_endpoint_base)

settings = Settings(values={"api_types": [APIType.KSERVE]})
serving = ServingTokenGeneratorSettings(
    model_factory=lambda: None,
    pipeline_config=config,
    tokenizer=None
)

app = fastapi_app(settings, serving)
matches = [r.path for r in app.routes if "cta" in r.path]
print("CTA ROUTES:", matches)
print("CTA IN MAX APP:", "/v2/cta/probe" in matches)
PY
