
podman run --rm -i \
  -v "$PWD:/cta:ro" -w /cta \
  --entrypoint /opt/venv/bin/python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import importlib.util
from fastapi import FastAPI
from fastapi.testclient import TestClient
from max.serve.api_server import ROUTES
from max.serve.config import APIType

path = "/cta/artifacts/v1.168-max/maxserve_cta_extension/cta_router.py"
spec = importlib.util.spec_from_file_location("cta_router", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.register_cta_routes()

app = FastAPI()
app.include_router(ROUTES[APIType.KSERVE].router)

response = TestClient(app).post("/v2/cta/probe")
print("HTTP STATUS:", response.status_code)
print("RESPONSE:", response.json())
assert response.status_code == 200
print("CTA ROUTER HTTP TEST: PASS")
PY
