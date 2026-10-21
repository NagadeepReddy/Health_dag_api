python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_spawn_worker.py")

code = '''"""Register CTA inside MAX's spawned worker via its model factory."""
import inspect

class CTAFactoryWrapper:
    def __init__(self, original_factory):
        self.original_factory = original_factory

    def __call__(self):
        from cta_worker_registration import install_cta_scheduler_hook
        install_cta_scheduler_hook()
        return self.original_factory()

def install_cta_spawn_entry():
    from max.serve.pipelines.model_worker import ModelWorker

    original = ModelWorker.start_model_worker
    signature = inspect.signature(original)
    assert "model_factory" in signature.parameters

    def wrapped(*args, **kwargs):
        bound = signature.bind(*args, **kwargs)
        factory = bound.arguments["model_factory"]
        bound.arguments["model_factory"] = CTAFactoryWrapper(factory)
        return original(*bound.args, **bound.kwargs)

    ModelWorker.start_model_worker = staticmethod(wrapped)
'''

compile(code, str(p), "exec")
p.write_text(code)
print("CTA SPAWN FACTORY: SYNTAX PASS")
PY
