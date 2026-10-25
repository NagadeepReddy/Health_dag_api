cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_native_live_server.py")
s = p.read_text()
anchor = 'print("LIVE DISPATCH MATCH:", rid in pending, flush=True)'

assert s.count(anchor) == 1, "Expected handoff trace missing"

if "CTA DIRECT HTTP BRIDGE" not in s:
    s = s.replace(anchor, anchor + '''
                # CTA DIRECT HTTP BRIDGE - LOCAL POC ONLY
                if rid in pending:
                    pending[rid].put_nowait(result[rid])
                    print("CTA HTTP BRIDGE ENQUEUED: YES", flush=True)
''', 1)

compile(s, str(p), "exec")
p.write_text(s)
print("CTA HTTP RESPONSE BRIDGE: READY")
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
