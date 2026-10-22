cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

PYTHONPATH="$PWD/artifacts/v1.168-max" python3 - <<'PY'
import sys, types

for name in ("max", "max.serve", "max.serve.pipelines"):
    m = types.ModuleType(name)
    m.__path__ = []
    sys.modules[name] = m

module = types.ModuleType("max.serve.pipelines.model_worker")

class ModelWorker:
    @staticmethod
    def start_model_worker(model_factory):
        return model_factory

module.ModelWorker = ModelWorker
sys.modules[module.__name__] = module

from maxserve_cta_extension.cta_spawn_worker import (
    CTAFactoryWrapper, install_cta_spawn_entry
)

install_cta_spawn_entry()
result = ModelWorker.start_model_worker(lambda: None)

assert isinstance(result, CTAFactoryWrapper)
print("MAX WORKER FACTORY WRAPPING: PASS")
print("PACKAGE IMPORT: PASS")
PY
