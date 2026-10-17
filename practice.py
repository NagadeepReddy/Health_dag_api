
podman run --rm -i --entrypoint /bin/bash \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  -lc '/opt/venv/bin/python -' <<'PY'
from max.serve.api_server import (
    fastapi_app, Settings,
    ServingTokenGeneratorSettings, ROUTES
)
from max.serve.config import APIType

async def cta_probe():
    return {"status": "ok"}

ROUTES[APIType.KSERVE].router.add_api_route(
    "/cta/probe", cta_probe, methods=["POST"]
)

settings = Settings(values={"api_types": [APIType.KSERVE]})
serving = ServingTokenGeneratorSettings(
    model_factory=lambda: None,
    pipeline_config=None,
    tokenizer=None
)

app = fastapi_app(settings, serving)
routes = [r.path for r in app.routes]
print("CTA ROUTE IN MAX APP:", "/v2/cta/probe" in routes)
print("MATCHING ROUTES:", [r for r in routes if "cta" in r])
PY
