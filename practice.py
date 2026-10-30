podman --root /application1/podman/storage --runroot /run/containers/storage exec -i -w /workspace -e PYTHONDONTWRITEBYTECODE=1 -e 'MAX_SERVE_API_TYPES=["openai","sagemaker","kserve"]' -e PYTHONPATH=/workspace/artifacts/v1.168-max/cta_native_batch2_release_candidate:/workspace/artifacts/v1.168/core-artifact:/batch2:/workspace/artifacts/v1.168-max a176e284b50a /opt/venv/bin/python -B - <<'PY'
import os
from max.serve.config import Settings, APIType
from max.serve.api_server import ROUTES
from maxserve_cta_extension.cta_router import register_cta_routes

settings = Settings()
print("API ENV:", os.environ["MAX_SERVE_API_TYPES"])
print("EFFECTIVE API TYPES:", [x.value for x in settings.api_types])

registered = register_cta_routes()
print("ROUTE REGISTRATION RESULT:", registered)

for api_type in settings.api_types:
    routes = [
        (r.path, sorted(r.methods or []))
        for r in ROUTES[api_type].router.routes
        if "/cta/" in r.path
    ]
    print("ACTIVE ROUTER:", api_type.value)
    print("CTA ROUTES:", routes)

kserve = APIType.KSERVE in settings.api_types
cta = any(
    r.path == "/v2/cta/probe" and "POST" in (r.methods or [])
    for r in ROUTES[APIType.KSERVE].router.routes
)

print("KSERVE CONFIGURED:", kserve)
print("CTA PROBE REGISTERED:", cta)
print("CONFIGURATION PREFLIGHT:", "PASS" if kserve and cta else "FAIL")
print("MAX EXECUTIONS: ZERO")
print("CONTAINERS RESTARTED: NONE")
PY
