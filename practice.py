PYTHONPATH=artifacts/v1.168-max/maxserve_cta_extension python3 - <<'PY'
import sys, types

events = []

for name in ("max", "max.serve", "max.serve.pipelines"):
    m = types.ModuleType(name)
    m.__path__ = []
    sys.modules[name] = m

worker = types.ModuleType("max.serve.pipelines.model_worker")

class ModelWorker:
    @staticmethod
    def _call():
        events.append("original_worker")

worker.ModelWorker = ModelWorker
sys.modules[worker.__name__] = worker

registration = types.ModuleType("cta_worker_registration")
registration.install_cta_scheduler_hook = lambda: events.append("cta_hook")
sys.modules[registration.__name__] = registration

from cta_spawn_worker import install_cta_spawn_entry

install_cta_spawn_entry()
ModelWorker._call()

assert events == ["cta_hook", "original_worker"], events
print("CTA WORKER WRAPPER: PASS")
print("HOOK ORDER: PASS")
PY
