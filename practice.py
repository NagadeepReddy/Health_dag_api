cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path

base = Path("artifacts/v1.168-max/maxserve_cta_extension")
router = base / "cta_router.py"
live = base / "cta_native_live_server.py"

s = router.read_text()
marker = "request_id = request.state.request_id"
fix = "queue._cta_http_loop = asyncio.get_running_loop()\n    "

if "queue._cta_http_loop = asyncio.get_running_loop()" not in s:
    assert s.count(marker) == 1
    s = s.replace(marker, fix + marker, 1)

compile(s, str(router), "exec")

t = live.read_text()
old = "pending[rid].put_nowait(result[rid])"
new = (
    "engine._cta_http_loop.call_soon_threadsafe("
    "pending[rid].put_nowait, result[rid])"
)

if new not in t:
    assert t.count(old) == 1
    t = t.replace(old, new, 1)

compile(t, str(live), "exec")

router.write_text(s)
live.write_text(t)

print("CTA THREAD-SAFE HTTP HANDOFF: READY")
print("ORIGINAL DS CODE: UNCHANGED")
PY

podman --root /application1/podman/storage \
  --runroot /run/containers/storage stop cta-native-live

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run -d --rm --name cta-native-live \
  --pull=never --network=none \
  -v "$PWD:/workspace:Z" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -u /workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_live_server.py
