cd /application1/sajjna8/rt-pzaas-v1.0 && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm -i --pull=never --network=none \
-v "$PWD:/workspace" -w /workspace \
--entrypoint python localhost/cta-max-faiss:local - <<'PY'
import sys, types, re, inspect, importlib.util, torch, traceback
from pathlib import Path

print("=== PZAAS RUNTIME MODEL RECOVERY ===", flush=True)

# Temporary scheduler shim: no background jobs will run.
class NoOpScheduler:
    def __init__(self, *a, **kw): pass
    def add_job(self, *a, **kw): return self
    def get_job(self, *a, **kw): return None
    def start(self, *a, **kw): pass
    def shutdown(self, *a, **kw): pass
    def modify(self, *a, **kw): return self

for name in (
    "apscheduler",
    "apscheduler.schedulers",
    "apscheduler.schedulers.background",
):
    m = types.ModuleType(name)
    m.__path__ = []
    sys.modules[name] = m

sys.modules["apscheduler.schedulers.background"].BackgroundScheduler = NoOpScheduler

base = Path("/workspace")
src = base / "artifacts/v1.472/core-artifact"
sys.path[:0] = [str(src), str(src.parent)]

class CaptureComplete(Exception):
    pass

try:
    spec = importlib.util.spec_from_file_location(
        "pzaas_runtime_capture", src / "pipeline.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    classes = [
        obj for obj in vars(module).values()
        if inspect.isclass(obj)
        and obj.__module__ == module.__name__
        and callable(getattr(obj, "loadBaseModel", None))
        and callable(getattr(obj, "load", None))
    ]

    assert len(classes) == 1, f"Loader classes found: {len(classes)}"
    cls = classes[0]
    original = cls.loadBaseModel

    def capture(self, *args, **kwargs):
        result = original(self, *args, **kwargs)
        suffix = str(kwargs.get("model_suffix", args[1] if len(args) > 1 else ""))

        if "base" not in suffix.lower():
            return result

        model = result[0] if isinstance(result, tuple) else result
        state = model.state_dict()

        layers = sorted({
            int(m.group(1))
            for k in state
            if (m := re.search(r"ptransformer\.(\d+)\.", k))
        })

        print("INITIALIZED LAYERS:", layers)
        print("RUNTIME STATE TENSORS:", len(state))

        extra = {
            k: v.detach().cpu()
            for k, v in state.items()
            if (m := re.search(r"ptransformer\.(\d+)\.", k))
            and int(m.group(1)) in (2, 3, 4, 5)
        }

        print("LAYERS 2-5 TENSORS:", len(extra))

        if extra:
            out = base / (
                "artifacts/v1.472-max/pzaas_max/validation/"
                "runtime_unverified_layers_2_5.pt"
            )
            out.parent.mkdir(parents=True, exist_ok=True)
            assert not out.exists(), "Snapshot exists; refusing overwrite"
            torch.save(extra, out)
            print("RUNTIME SNAPSHOT: SAVED")
            print("TRAINING PROVENANCE: NOT VERIFIED")
        else:
            print("RUNTIME SNAPSHOT: NO ADDITIONAL LAYERS")

        raise CaptureComplete()

    cls.loadBaseModel = capture
    try:
        cls().load()
    except CaptureComplete:
        print("RUNTIME CAPTURE: PASS")
    else:
        print("RUNTIME CAPTURE: NO BASE MODEL INTERCEPTED")

except Exception:
    traceback.print_exc(limit=5)
    print("RUNTIME CAPTURE: BLOCKED")

print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
print("NEXT: VERIFY TRAINED WEIGHTS AND FULL NUMERICAL PARITY")
PY
