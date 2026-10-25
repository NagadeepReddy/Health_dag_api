cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path
import re

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_http_pipeline.py")
s = p.read_text()

pattern = re.compile(
    r'(?m)^([ \t]*)self\.create_background_task\(\s*'
    r'self\._engine_queue\.response_worker,\s*\)\s*\n'
    r'[ \t]*print\("CTA_RESPONSE_WORKER_STARTED", flush=True\)'
)

matches = list(pattern.finditer(s))
assert len(matches) == 1, "Expected response-worker hook not found"

m = matches[0]
indent = m.group(1)

replacement = (
    indent + "self.create_background_task(\n"
    + indent + "    lambda: _cta_wait_for_healthy_worker(self._engine_queue)\n"
    + indent + ")\n"
    + indent + 'print("CTA RECEIVER WAIT HOOK INSTALLED", flush=True)'
)

s = s[:m.start()] + replacement + s[m.end():]

helper = '''
async def _cta_wait_for_healthy_worker(engine_queue):
    import asyncio
    print("CTA RECEIVER: WAITING FOR WORKER HEALTH", flush=True)
    for _ in range(240):
        if engine_queue.is_worker_healthy():
            print("CTA RECEIVER: WORKER HEALTHY, STARTING", flush=True)
            await engine_queue.response_worker()
            return
        await asyncio.sleep(0.5)
    raise RuntimeError("CTA worker health never became ready")

'''

anchor = "class CTANativeHTTPPipeline("
assert anchor in s
s = s.replace(anchor, helper + anchor, 1)

compile(s, str(p), "exec")
p.with_suffix(".py.before_health_fix").write_text(p.read_text())
p.write_text(s)

print("CTA RESPONSE STARTUP ORDER: FIXED")
print("SYNTAX: PASS")
print("DS CODE: UNCHANGED")
PY

P="podman --root /application1/podman/storage --runroot /run/containers/storage"

$P run -d --replace --name cta-native-live \
  --pull=never --network=none \
  -v "$PWD:/workspace:Z" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -u /workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_live_server.py

sleep 15
$P logs cta-native-live 2>&1 | grep -E \
'CTA RECEIVER|startup complete|Uvicorn running|Worker failed|Traceback|ERROR' | tail -15
