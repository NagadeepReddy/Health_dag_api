cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  -v "$PWD:/workspace:ro" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -c '
from max.serve import api_server
from max.serve.config import Settings
from maxserve_cta_extension.cta_router import register_cta_routes

register_cta_routes()
print("DEFAULT API:", Settings().api_type)
print("KSERVE CTA ROUTES:", [
    r.path for r in api_server.ROUTES[api_server.APIType.KSERVE].router.routes
    if "cta" in r.path
])
'
