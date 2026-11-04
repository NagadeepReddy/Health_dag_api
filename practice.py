cd /application1/sajjna8/rt-pzaas-v1.0 && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm -i --pull=never --network=none \
-v "$PWD:/workspace" -w /workspace \
--entrypoint python localhost/cta-max-faiss:local - <<'PY'
import sys, types, re, inspect, importlib.util, traceback
from pathlib import Path

print("=== PZAAS RUNTIME RECOVERY ===", flush=True)

class NoOp:
    def __init__(self, *args, **kwargs):
        pass
    def add_job(self, *args, **kwargs):
        return self
    def get_job(self, *args, **kwargs):
        return self
    def modify(self, *args, **kwargs):
        return self
    def start(self, *args, **kwargs):
        pass
    def shutdown(self, *args, **kwargs):
        pass

names = [
    "apscheduler",
    "apscheduler.schedulers",
    "apscheduler.schedulers.background",
    "apscheduler.triggers",
    "apscheduler.triggers.interval",
    "apscheduler.triggers.cron",
    "apscheduler.triggers.date",
]

for name in names:
    module = types.ModuleType(name)
    module.__path__ = []
    sys.modules[name] = module

sys.modules["apscheduler.schedulers.background"].BackgroundScheduler = NoOp
sys.modules["apscheduler.triggers.interval"].IntervalTrigger = NoOp
sys.modules["apscheduler.triggers.cron"].CronTrigger = NoOp
sys.modules["apscheduler.triggers.date"].DateTrigger = NoOp

print("SCHEDULER IMPORT SHIMS: PASS")

root = Path("/workspace")
source = root / "artifacts/v1.472/core-artifact"

sys.path[:0] = [str(source), str(source.parent)]

class CaptureDone(Exception):
    pass

try:
    spec = importlib.util.spec_from_file_location(
        "pzaas_capture",
        source / "pipeline.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    print("PIPELINE IMPORT: PASS")

    classes = [
        obj for obj in vars(module).values()
        if inspect.isclass(obj)
        and obj.__module__ == module.__name__
        and callable(getattr(obj, "loadBaseModel", None))
        and callable(getattr(obj, "load", None))
    ]

    print("LOADER CLASSES:", [c.__name__ for c in classes])

    assert len(classes) == 1, "Loader class not unique"

    cls = classes[0]
    original = cls.loadBaseModel

    def capture(self, *args, **kwargs):
        result = original(self, *args, **kwargs)

        suffix = str(kwargs.get(
            "model_suffix",
            args[1] if len(args) > 1 else ""
        ))

        if suffix != "base":
            return result

        model = result[0] if isinstance(result, tuple) else result

        state = model.state_dict()

        layers = sorted({
            int(match.group(1))
            for key in state
            if (match := re.search(
                r"ptransformer\.(\d+)\.", key
            ))
        })

        print("RUNTIME MODEL:", type(model).__name__)
        print("RUNTIME LAYERS:", layers)
        print("RUNTIME TENSORS:", len(state))

        for layer in range(6):
            keys = [
                k for k in state
                if f"ptransformer.{layer}." in k
            ]
            print(f"LAYER {layer}: {len(keys)} tensors")

        print("REFERENCE EXPORTED TRAINED LAYERS: [0, 1]")
        print("INITIALIZED IS NOT NECESSARILY TRAINED")
        print("RUNTIME INSPECTION: PASS")
        raise CaptureDone()

    cls.loadBaseModel = capture

    try:
        cls().load()
    except CaptureDone:
        print("RUNTIME CAPTURE: PASS")
    else:
        print("RUNTIME CAPTURE: BASE MODEL NOT INTERCEPTED")

except Exception:
    traceback.print_exc(limit=5)
    print("RUNTIME CAPTURE: BLOCKED")

print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
print("NEXT: VERIFY WEIGHT PROVENANCE BEFORE FULL PARITY")
PY
