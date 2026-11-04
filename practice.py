cd /application1/sajjna8/rt-pzaas-v1.0 && \
V="$PWD/artifacts/v1.472-max/pzaas_max/validation" && \
mkdir -p "$V/python_deps" && \
cp /vzwhome/sajjna8/einops-0.8.1-py3-none-any.whl "$V/" && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm -i --network none --memory 10g \
--tmpfs /tmp:rw,size=1g \
-e HOME=/tmp \
-e PYTHONDONTWRITEBYTECODE=1 \
-e PYTHONPATH=/validation/python_deps:/workspace/artifacts/v1.472/core-artifact:/workspace/artifacts/v1.472/utils/dependency-utils \
-v "$PWD:/workspace:ro" \
-v "$V:/validation:rw" \
-w /workspace \
--entrypoint /bin/sh \
localhost/cta-max-faiss:local -c '
/opt/venv/bin/python -m pip install \
--no-index --no-deps \
--target /validation/python_deps \
/validation/einops-0.8.1-py3-none-any.whl &&
/opt/venv/bin/python -u -' <<'PY'
import sys, types, json, traceback
import numpy as np

print("=== PZAAS REAL INPUT CAPTURE ===")

import einops
print("REAL EINOPS:", einops.__version__)

# Offline validation only; original DS remains unchanged.
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
    def add_job(self, *a, **kw): pass
    def start(self): pass

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
    from pipeline import pipeline

    ds = pipeline()
    if not getattr(ds, "loaded", False):
        ds.load()

    print("ORIGINAL DS LOAD: PASS")

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
            print(name, value.shape, value.dtype)

    assert arrays, "No model tensors captured"

    np.savez_compressed(
        "/validation/sanity_model_inputs.npz", **arrays
    )

    print("PZAAS REAL INPUT CAPTURE: PASS")
    print("CAPTURED TENSORS:", len(arrays))
    print("ORIGINAL DS: UNCHANGED")
    print("MAX INFERENCE / PARITY: NEXT")

except Exception:
    traceback.print_exc()
    raise SystemExit("INPUT CAPTURE: BLOCKED")
PY
