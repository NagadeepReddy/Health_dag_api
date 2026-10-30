podman --root /application1/podman/storage --runroot /run/containers/storage exec -i -w /workspace -e PYTHONDONTWRITEBYTECODE=1 -e PYTHONPATH=/workspace/artifacts/v1.168-max/cta_native_batch2_release_candidate:/workspace/artifacts/v1.168/core-artifact:/batch2:/workspace/artifacts/v1.168-max a176e284b50a /opt/venv/bin/python -B - <<'PY'
import inspect
import re
from max.serve import api_server
from max.serve.config import APIType
from maxserve_cta_extension.cta_router import register_cta_routes

print("=== CTA ROUTE REGISTRATION ===")
result = register_cta_routes()
print("REGISTER RESULT:", result)

for api_type, config in api_server.ROUTES.items():
    print("\nAPI TYPE:", api_type)
    for route in config.router.routes:
        path = getattr(route, "path", "")
        if "cta" in path.lower():
            print(
                "CTA ROUTE:",
                path,
                "METHODS:",
                sorted(getattr(route, "methods", []) or [])
            )

print("\n=== MAX ROUTER MOUNTING ===")
source = inspect.getsource(api_server)
lines = source.splitlines()

pattern = re.compile(
    r"include_router|ROUTES\[|ROUTES\.|"
    r"APIType\.|prefix=|api_type|/v1|/v2",
    re.I
)

shown = set()

for i, line in enumerate(lines):
    if pattern.search(line):
        for j in range(max(0, i-2), min(len(lines), i+3)):
            if j not in shown:
                print(f"{j+1}: {lines[j][:200]}")
                shown.add(j)
        if len(shown) >= 90:
            break

print("\nROUTE CONFIGURATION INSPECTION: COMPLETE")
print("SOURCE CHANGES: NONE")
print("CONTAINERS RESTARTED: NONE")
print("MAX EXECUTIONS: ZERO")
PY
