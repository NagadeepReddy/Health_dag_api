
podman run --rm --entrypoint /bin/bash \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  -lc '/opt/venv/bin/python -c "
from max.serve.api_server import ROUTES
from max.serve.config import APIType

router = ROUTES[APIType.KSERVE].router
before = len(router.routes)

async def cta_probe():
    return {\"status\": \"CTA route registered\"}

router.add_api_route(\"/cta/probe\", cta_probe, methods=[\"POST\"])

assert len(router.routes) == before + 1
print(\"NATIVE ROUTER EXTENSION: PASS\")
print(\"CTA route:\", router.routes[-1].path)
"'
