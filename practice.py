
cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
timeout -k 5s 30s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  --memory=2g \
  -v "$PWD:/work:ro" -w /work \
  -e PYTHONPATH=/work/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -c '
from maxserve_cta_extension.cta_router import (
    register_cta_routes, ROUTES, APIType
)
register_cta_routes()
routes = ROUTES[APIType.KSERVE].router.routes
for r in routes:
    if "cta" in r.path:
        print(r.path, r.methods)
assert any(
    r.path.endswith("/cta/infer") and "POST" in r.methods
    for r in routes
)
print("NATIVE CTA ROUTE REGISTRATION: PASS")
'
