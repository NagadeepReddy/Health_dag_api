cd /application1/sajjna8/rt-pzaas-v1.0 && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage run --rm -i \
--network none --memory 10g \
--tmpfs /tmp:rw,size=1g \
-e PYTHONDONTWRITEBYTECODE=1 \
-e PYTHONPATH=/workspace/artifacts/v1.472/core-artifact:/workspace/artifacts/v1.472/utils/dependency-utils \
-v "$PWD:/workspace:ro" \
-v "$PWD/artifacts/v1.472-max/pzaas_max/validation:/validation:rw" \
-w /workspace \
--entrypoint python3 localhost/cta-max-faiss:local -u - <<'PY'
import sys, types, json, traceback
import numpy as np

print("=== PZAAS REAL INPUT CAPTURE ===", flush=True)

# Offline testing only: disable background refresh jobs.
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
    def __init__(self, *a, **kw): pass
    def add_job(self, *a, **kw): pass
    def start(self): pass
    def shutdown(self, *a, **kw): pass

class IntervalTrigger:
    def __init__(self, *a, **kw): pass

sys.modules[
    "apscheduler.schedulers.background"
].BackgroundScheduler = BackgroundScheduler

sys.modules[
    "apscheduler.triggers.interval"
].IntervalTrigger = IntervalTrigger

print("OFFLINE SCHEDULER ISOLATION: PASS", flush=True)

try:
    from pipeline import pipeline

    ds = pipeline()
    print("DS INITIALIZATION: PASS", flush=True)

    if not getattr(ds, "loaded", False):
        ds.load()

    print("DS LOAD: PASS", flush=True)

    with open("artifacts/v1.472/samples/sanity_input.json") as f:
        body = json.load(f)

    model_in = ds.preprocess(body)[0]

    assert isinstance(model_in, dict)
    print("REAL DS PREPROCESS: PASS", flush=True)

    arrays = {}
    for name, value in model_in.items():
        if hasattr(value, "detach"):
            value = value.detach().cpu().numpy()
        if isinstance(value, np.ndarray):
            arrays[name] = value
            print("INPUT:", name, value.shape, flush=True)

    assert arrays, "No model tensors captured"

    np.savez_compressed(
        "/validation/sanity_model_inputs.npz",
        **arrays
    )

    print("PZAAS REAL INPUT CAPTURE: PASS")
    print("CAPTURED TENSORS:", len(arrays))
    print("ORIGINAL DS: UNCHANGED")
    print("MAX INFERENCE / PARITY: NEXT")

except Exception:
    traceback.print_exc()
    raise SystemExit("PZAAS REAL INPUT CAPTURE: FAILED")
PY
