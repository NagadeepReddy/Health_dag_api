cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_router.py")
s = p.read_text()
anchor = "output = await response_queue.get()"
trace = '''output = await response_queue.get()
                    print(
                        "CTA HTTP QUEUE ITEM:",
                        type(output).__name__,
                        "result_type=",
                        type(getattr(output, "result", None)).__name__,
                        "result=",
                        repr(getattr(output, "result", None))[:300],
                        flush=True,
                    )'''

if "CTA HTTP QUEUE ITEM:" not in s:
    assert s.count(anchor) == 1, "Expected router location not found"
    s = s.replace(anchor, trace, 1)

compile(s, str(p), "exec")
p.write_text(s)
print("CTA HTTP HANDLER TRACE: READY")
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
