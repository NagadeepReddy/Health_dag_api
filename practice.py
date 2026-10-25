cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path
import re

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_http_pipeline.py")
s = p.read_text()

if "CTA_RESPONSE_WORKER_STARTED" not in s:
    pattern = r'^([ \t]*)print\("CTA QUEUE INITIALIZED:"'
    m = re.search(pattern, s, re.M)
    assert m, "Queue initialization marker not found"

    indent = m.group(1)
    hook = (
        indent + "self.create_background_task(\n"
        + indent + "    self._engine_queue.response_worker,\n"
        + indent + '    task_name="cta_response_worker",\n'
        + indent + ")\n"
        + indent + 'print("CTA_RESPONSE_WORKER_STARTED", flush=True)\n'
    )
    s = s[:m.start()] + hook + s[m.start():]

compile(s, str(p), "exec")
p.write_text(s)
print("CTA RESPONSE WORKER HOOK: INSTALLED")
PY

P="podman --root /application1/podman/storage --runroot /run/containers/storage"

$P stop -t 5 cta-native-live >/dev/null 2>&1 || true

$P run -d --rm --name cta-native-live \
  --pull=never --network=none \
  -v "$PWD:/workspace:Z" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -u /workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_live_server.py

sleep 8
$P logs cta-native-live 2>&1 | grep -E \
'CTA_RESPONSE_WORKER_STARTED|startup complete|Uvicorn running|Traceback|ERROR' | tail -12
