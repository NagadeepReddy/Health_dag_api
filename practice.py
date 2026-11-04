cd /application1/sajjna8/rt-pzaas-v1.0 && \
mkdir -p artifacts/v1.472-max/pzaas_max/validation && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm -i --network none --memory 10g \
--tmpfs /tmp:rw,size=1g \
-e HOME=/tmp \
-e PYTHONDONTWRITEBYTECODE=1 \
-e PYTHONPATH=/workspace/artifacts/v1.472/core-artifact:/workspace/artifacts/v1.472/utils/dependency-utils \
-v "$PWD:/workspace:ro" \
-v "$PWD/artifacts/v1.472-max/pzaas_max/validation:/validation:rw" \
-w /workspace \
--entrypoint /opt/venv/bin/python \
localhost/cta-max-faiss:local -u - <<'PY'
import sys, types, json, traceback
import numpy as np

print("=== PZAAS REAL DS INPUT CAPTURE ===", flush=True)
print("PYTHON:", sys.executable)

# Disable only background scheduling in offline validation.
for name in (
    "apscheduler",
    "apscheduler.schedulers",
    "apscheduler.schedulers.background",
    "apscheduler.triggers",
    "apscheduler.triggers.interval",
):
    m = types.ModuleType(name)
    m.__path__ = []
    sys.modules[name] = m

class BackgroundScheduler:
    def __init__(self, *a, **k): pass
    def add_job(self, *a, **k): pass
    def start(self): pass

class IntervalTrigger:
    def __init__(self, *a, **k): pass

sys.modules["apscheduler.schedulers.background"].BackgroundScheduler = BackgroundScheduler
sys.modules["apscheduler.triggers.interval"].IntervalTrigger = IntervalTrigger

try:
    import torch
    import einops
    from pipeline import pipeline

    print("DS IMPORTS: PASS", flush=True)

    ds = pipeline()
    if not getattr(ds, "loaded", False):
        ds.load()

    print("DS LOAD: PASS", flush=True)

    with open("artifacts/v1.472/samples/sanity_input.json") as f:
        body = json.load(f)

    model_in = ds.preprocess(body)[0]
    assert isinstance(model_in, dict)

    arrays = {}
    for name, value in model_in.items():
        if isinstance(value, torch.Tensor):
            value = value.detach().cpu().numpy()
        if isinstance(value, np.ndarray):
            arrays[name] = value
            print("INPUT:", name, value.shape, value.dtype)

    assert arrays, "No model tensors captured"

    np.savez_compressed(
        "/validation/sanity_model_inputs.npz",
        **arrays
    )

    print("REAL PZAAS INPUT CAPTURE: PASS")
    print("CAPTURED:", len(arrays))
    print("ORIGINAL DS: UNCHANGED")
    print("REAL MAX INFERENCE: NEXT")

except Exception:
    traceback.print_exc()
    raise SystemExit("INPUT CAPTURE: BLOCKED")
PY
