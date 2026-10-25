cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_http_pipeline.py")
s = p.read_text()
marker = "class CTANativeHTTPPipeline("

assert marker in s, "CTA pipeline class not found"

if "CTA_ZMQ_EMPTY_COMPAT_FIX" not in s:
    patch = '''
# CTA_ZMQ_EMPTY_COMPAT_FIX: local MAX/ZMQ compatibility
import queue as _cta_std_queue
import zmq as _cta_zmq
from max.serve.queue.zmq_queue import ZmqPullSocket as _CTAPullSocket

_cta_original_get_nowait = _CTAPullSocket.get_nowait

def _cta_safe_get_nowait(self):
    try:
        return _cta_original_get_nowait(self)
    except _cta_zmq.Again:
        raise _cta_std_queue.Empty from None

_CTAPullSocket.get_nowait = _cta_safe_get_nowait
print("CTA ZMQ EMPTY HANDLING: INSTALLED", flush=True)

'''
    updated = s.replace(marker, patch + marker, 1)
    compile(updated, str(p), "exec")
    p.with_suffix(".py.before_zmq_fix").write_text(s)
    p.write_text(updated)

print("CTA ZMQ EMPTY HANDLING: SYNTAX PASS")
print("ORIGINAL DS CODE: UNCHANGED")
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
$P logs --tail 50 cta-native-live 2>&1 | grep -E \
'CTA ZMQ EMPTY|CTA RECEIVER|startup complete|Uvicorn running|Worker failed|Traceback|ERROR'
