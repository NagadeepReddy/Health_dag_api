cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_native_e2e_test.py")
s = p.read_text()

patch = '''
# CTA-only native queue compatibility.
from typing import Any
import importlib

_cta_queues = importlib.import_module("max.serve.scheduler.queues")
_cta_original_init = _cta_queues.SchedulerZmqConfigs.__init__

def _cta_queue_init(self, pipeline_task):
    _cta_original_init(self, pipeline_task)
    self.request_queue_config = _cta_queues.ZmqConfig[Any](Any)

_cta_queues.SchedulerZmqConfigs.__init__ = _cta_queue_init
'''

if "_cta_queue_init" not in s:
    anchor = "from types import SimpleNamespace"
    assert anchor in s, "Expected test structure missing; no changes made"
    s = s.replace(anchor, patch + "\n" + anchor, 1)
    compile(s, str(p), "exec")
    p.write_text(s)

print("CTA NATIVE JSON QUEUE PATCH: SYNTAX PASS")
print("ORIGINAL DS CODE: UNCHANGED")
PY

timeout 150s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  -v "$PWD:/workspace:Z" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -u /workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_e2e_test.py

echo "E2E EXIT CODE: $?"
