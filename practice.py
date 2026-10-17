
podman run --rm -i \
  -v "$PWD:/cta:ro" -w /cta \
  --entrypoint /opt/venv/bin/python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import importlib.util
from pathlib import Path
from max.serve.api_server import ROUTES
from max.serve.config import APIType

path = Path("/cta/artifacts/v1.168-max/maxserve_cta_extension/cta_router.py")
spec = importlib.util.spec_from_file_location("cta_router", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

router = ROUTES[APIType.KSERVE].router

first = module.register_cta_routes()
second = module.register_cta_routes()

matches = [r for r in router.routes if r.path == "/v2/cta/probe"]

assert first is True
assert second is False
assert len(matches) == 1

print("CTA ROUTER MODULE: PASS")
print("CTA ROUTE:", matches[0].path)
print("DUPLICATE REGISTRATION: PREVENTED")
PY
