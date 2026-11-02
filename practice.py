python3 - <<'PY'
from pathlib import Path
import ast

p = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_native_serve_dev/bplan_native_launcher.py")
s = p.read_text()

assert "api_server.fastapi_app(" in s, "STOP: MAX app creation missing"
assert "uvicorn.run(app," in s, "STOP: expected launcher structure missing"

marker = "    uvicorn.run(app,"
assert s.count(marker) == 1, "STOP: unexpected launcher structure"

patch = '''    # Register BPLAN on the actual built-in MAX Serve ASGI app.
    from bplan_native_serve_dev.bplan_router import bplan_predict
    if not any(getattr(r, "path", None) == "/bplan/predict" for r in app.routes):
        app.add_api_route("/bplan/predict", bplan_predict, methods=["POST"])
    assert any(getattr(r, "path", None) == "/bplan/predict" for r in app.routes)
    print("BPLAN ACTUAL MAX HTTP ROUTE: PASS", flush=True)

'''

if "BPLAN ACTUAL MAX HTTP ROUTE: PASS" not in s:
    s = s.replace(marker, patch + marker, 1)
    ast.parse(s)
    p.write_text(s)

print("BPLAN ROUTE FIX: PASS")
print("ORIGINAL DS AND CTA: UNCHANGED")
PY
