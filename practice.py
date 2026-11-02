DEV=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_native_serve_dev

DEV="$DEV" python3 - <<'PY'
import os, ast
from pathlib import Path

path = Path(os.environ["DEV"]) / "bplan_native_launcher.py"
router = path.parent / "bplan_router.py"

assert path.is_file() and router.is_file()

src = path.read_text()
old = "    register_bplan_architecture()\n"

new = """    register_bplan_architecture()

    from bplan_native_serve_dev.bplan_router import register_bplan_routes
    register_bplan_routes()
    print("BPLAN NATIVE HTTP ROUTES: REGISTERED", flush=True)
"""

assert src.count(old) == 1, "STOP: unexpected launcher structure"
assert "register_bplan_routes" not in src, "STOP: already wired"

updated = src.replace(old, new, 1)
ast.parse(updated)
path.write_text(updated)

print("BPLAN HTTP-LAUNCHER WIRING: PASS")
print("BPLAN ENDPOINT: /bplan/predict")
print("ORIGINAL DS AND CTA: UNCHANGED")
PY
