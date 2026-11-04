cd /application1/sajjna8/rt-pzaas-v1.0 && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm -i --pull=never --network=none \
-v "$PWD:/workspace" -w /workspace \
--entrypoint python \
localhost/cta-max-faiss:local - <<'PY'
import sys, inspect, importlib.util, re, torch
from pathlib import Path

base = Path("/workspace")
src = base / "artifacts/v1.472/core-artifact"
sys.path[:0] = [str(src), str(src.parent)]

spec = importlib.util.spec_from_file_location(
    "pzaas_original_capture", src / "pipeline.py"
)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

classes = [
    c for c in vars(mod).values()
    if inspect.isclass(c)
    and c.__module__ == mod.__name__
    and callable(getattr(c, "loadBaseModel", None))
    and callable(getattr(c, "load", None))
]

assert len(classes) == 1, "Original loader class not uniquely found"
cls = classes[0]
original = cls.loadBaseModel
captured = []

def capture(self, *args, **kwargs):
    result = original(self, *args, **kwargs)
    model = result[0] if isinstance(result, tuple) else result
    state = model.state_dict()
    layers = sorted({
        int(m.group(1))
        for key in state
        if (m := re.search(r"ptransformer\.(\d+)\.", key))
    })
    print("ACTUAL INITIALIZED LAYERS:", layers)
    captured.extend(layers)

    missing = {
        k: v.detach().cpu()
        for k, v in state.items()
        if (m := re.search(r"ptransformer\.(\d+)\.", k))
        and int(m.group(1)) in (2, 3, 4, 5)
    }

    if missing:
        dst = base / "artifacts/v1.472-max/pzaas_max/validation/runtime_initialized_layers_2_5.pt"
        assert not dst.exists(), "Snapshot already exists; refusing overwrite"
        dst.parent.mkdir(parents=True, exist_ok=True)
        torch.save(missing, dst)
        print("RUNTIME SNAPSHOT SAVED:", dst)
        print("TENSORS:", len(missing))
        print("NOTE: Initialized does not mean trained")
    return result

cls.loadBaseModel = capture

print("=== PZAAS ORIGINAL RUNTIME CAPTURE ===")
try:
    cls().load()
except Exception as exc:
    print("LOADER EXIT:", type(exc).__name__, str(exc)[:200])

print("RUNTIME CAPTURE:", "PASS" if captured else "BLOCKED")
print("ORIGINAL DS FILES: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
print("NEXT: VALIDATE REAL MODEL DEPTH AND NUMERICAL PARITY")
PY
