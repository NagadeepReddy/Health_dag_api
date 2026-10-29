python3 -S -B - <<'PY'
from pathlib import Path
import ast
import shutil

p = Path("/application1/cta_max_native_release_candidate_20261028/cta_native_launcher.py")
assert p.is_file(), "STOP: release launcher missing"

source = p.read_text()
anchor = '    sys.argv = ["max.entrypoints.pipelines", "serve", *sys.argv[1:]]'
marker = "# CTA_NATIVE_TYPED_QUEUE_BRIDGE"

assert source.count(anchor) == 1, "STOP: launcher structure differs"
assert marker not in source, "STOP: queue bridge already installed"

patch = '''
    # CTA_NATIVE_TYPED_QUEUE_BRIDGE
    # Match the proven CTA TestClient queue configuration.
    from typing import Any as _CTAAny
    from max.serve.scheduler import queues as _cta_queues
    from max.interfaces.request import RequestID
    from max.interfaces.scheduler import SchedulerResult
    from maxserve_cta_extension.cta_native_scheduler import CTASerializableOutput

    _cta_original_init = _cta_queues.SchedulerZmqConfigs.__init__

    def _cta_queue_init(self, pipeline_task):
        _cta_original_init(self, pipeline_task)
        self.request_queue_config = _cta_queues.ZmqConfig[_CTAAny](_CTAAny)
        response_type = dict[RequestID, SchedulerResult[CTASerializableOutput]]
        self.response_queue_config = _cta_queues.ZmqConfig[response_type](
            response_type
        )

    _cta_queues.SchedulerZmqConfigs.__init__ = _cta_queue_init
    print("CTA NATIVE QUEUE BRIDGE: INSTALLED", flush=True)

'''

updated = source.replace(anchor, patch + anchor)
ast.parse(updated)

backup = p.with_name("cta_native_launcher.py.before_queue_bridge.bak")
assert not backup.exists(), "STOP: backup already exists"

shutil.copy2(p, backup)
p.write_text(updated)

assert marker in p.read_text()
print("QUEUE CONFIGURATION: UPDATED")
print("REQUEST FORMAT: Any / CTA JSON")
print("RESPONSE FORMAT: CTA SerializableOutput")
print("PYTHON SYNTAX: PASS")
print("BACKUP: CREATED")
print("DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
