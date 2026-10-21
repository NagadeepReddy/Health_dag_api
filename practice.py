PYTHONPATH=artifacts/v1.168-max/maxserve_cta_extension python3 - <<'PY'
import pickle
import sys
import types

events = []

class FakeFactory:
    def __call__(self):
        events.append("model_created")
        return "MODEL"

registration = types.ModuleType("cta_worker_registration")
registration.install_cta_scheduler_hook = lambda: events.append("cta_hook")
sys.modules["cta_worker_registration"] = registration

from cta_spawn_worker import CTAFactoryWrapper

factory = pickle.loads(pickle.dumps(CTAFactoryWrapper(FakeFactory())))
assert factory() == "MODEL"
assert events == ["cta_hook", "model_created"], events

print("FACTORY SERIALIZATION: PASS")
print("CTA HOOK BEFORE MODEL: PASS")
PY
