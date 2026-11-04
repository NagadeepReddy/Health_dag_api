cd /application1/sajjna8/rt-pzaas-v1.0 && \
V="$PWD/artifacts/v1.472-max/pzaas_max/validation" && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm -i --pull=never \
--network none --memory 10g \
--tmpfs /tmp:rw,size=1g \
-e HOME=/tmp \
-e PYTHONDONTWRITEBYTECODE=1 \
-e PYTHONPATH=/validation/python_deps:/workspace/artifacts/v1.472/core-artifact:/workspace/artifacts/v1.472/utils/dependency-utils \
-v "$PWD:/workspace:ro" \
-v "$V:/validation:rw" \
-w /workspace \
--entrypoint /opt/venv/bin/python \
localhost/cta-max-faiss:local -u - <<'PY'
import sys, types, json, traceback
import numpy as np

print("=== PZAAS REAL INPUT CAPTURE ===", flush=True)

# Import compatibility for offline validation only.
for name in (
    "apscheduler",
    "apscheduler.schedulers",
    "apscheduler.schedulers.background",
    "apscheduler.triggers",
    "apscheduler.triggers.interval",
):
    module = types.ModuleType(name)
    module.__path__ = []
    sys.modules[name] = module

class BackgroundScheduler:
    def __init__(self, *a, **kw): pass

class IntervalTrigger:
    def __init__(self, *a, **kw): pass

sys.modules[
    "apscheduler.schedulers.background"
].BackgroundScheduler = BackgroundScheduler

sys.modules[
    "apscheduler.triggers.interval"
].IntervalTrigger = IntervalTrigger

try:
    import torch
    import einops, joblib, sklearn, cloudpickle
    import threadpoolctl, scipy

    print("RUNTIME DEPENDENCIES: PASS", flush=True)

    from pipeline import pipeline

    # Disable only periodic refresh scheduling for this process.
    # Original source files remain untouched.
    pipeline.schedule_pull = lambda self: None

    print("OFFLINE SCHEDULER ISOLATION: PASS", flush=True)

    ds = pipeline()
    if not getattr(ds, "loaded", False):
        ds.load()

    print("ORIGINAL DS MODEL LOAD: PASS", flush=True)

    with open(
        "artifacts/v1.472/samples/sanity_input.json"
    ) as f:
        body = json.load(f)

    result = ds.preprocess(body)
    model_in = result[0]

    assert isinstance(model_in, dict)

    print("ORIGINAL DS PREPROCESS: PASS", flush=True)
    print("MODEL INPUT FIELDS:", len(model_in))

    arrays = {}

    for name, value in model_in.items():
        if isinstance(value, torch.Tensor):
            value = value.detach().cpu().numpy()

        if isinstance(value, np.ndarray):
            arrays[name] = value
            print("INPUT:", name, value.shape, value.dtype)
        else:
            print("NON-ARRAY FIELD:", name, type(value).__name__)

    assert arrays, "No model tensors captured"

    np.savez_compressed(
        "/validation/sanity_model_inputs.npz",
        **arrays
    )

    print("PZAAS REAL INPUT CAPTURE: PASS")
    print("CAPTURED TENSORS:", len(arrays))
    print("ORIGINAL DS FILES: UNCHANGED")
    print("MAX INFERENCE / PARITY: NEXT")

except Exception:
    traceback.print_exc()
    raise SystemExit("PZAAS INPUT CAPTURE: BLOCKED")
PY
