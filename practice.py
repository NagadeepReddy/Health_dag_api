
python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_router.py")

if p.exists():
    raise SystemExit("STOP: Extension file already exists")

p.write_text('''from max.serve.api_server import ROUTES
from max.serve.config import APIType

async def cta_probe():
    return {"status": "CTA MAX Serve extension ready"}

def register_cta_routes():
    router = ROUTES[APIType.KSERVE].router

    if any(r.path == "/v2/cta/probe" for r in router.routes):
        return False

    router.add_api_route(
        "/cta/probe",
        cta_probe,
        methods=["POST"],
    )
    return True
''')

print("ISOLATED CTA ROUTER MODULE CREATED")
print(p)
PY
