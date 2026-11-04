cd /application1/sajjna8/rt-pzaas-v1.0 && \
V="$PWD/artifacts/v1.472-max/pzaas_max/validation" && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm -i --network none --memory 10g \
--tmpfs /tmp:rw,size=1g \
-e HOME=/tmp \
-e PYTHONDONTWRITEBYTECODE=1 \
-e PYTHONPATH=/validation/python_deps:/workspace/artifacts/v1.472/core-artifact:/workspace/artifacts/v1.472/utils/dependency-utils \
-v "$PWD:/workspace:ro" \
-v "$V:/validation:rw" \
-v /vzwhome/sajjna8:/wheels:ro \
-w /workspace \
--entrypoint /bin/sh \
localhost/cta-max-faiss:local -ec '
/opt/venv/bin/python -m pip install \
  --no-index --no-deps --no-cache-dir \
  --target /validation/python_deps \
  /wheels/cloudpickle-3.1.1-py3-none-any.whl

/opt/venv/bin/python -u -' <<'PY'
import sys, types, json, traceback
import numpy as np

print("=== PZAAS REAL INPUT CAPTURE ===", flush=True)

import einops, joblib, sklearn, cloudpickle

print("EINOPS: PASS")
print("JOBLIB: PASS")
print("SCIKIT-LEARN: PASS")
print("CLOUDPICKLE: PASS")

# Offline validation only. No original DS changes.
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

    print("ORIGINAL DS IMPORT: PASS", flush=True)

    ds = pipeline()

    if not getattr(ds, "loaded", False):
        ds.load()

    print("ORIGINAL DS LOAD: PASS", flush=True)

    with open(
        "artifacts/v1.472/samples/sanity_input.json"
    ) as f:
        body = json.load(f)

    result = ds.preprocess(body)
    model_in = result[0]

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

    print("PZAAS REAL INPUT CAPTURE: PASS")
    print("CAPTURED TENSORS:", len(arrays))
    print("ORIGINAL DS: UNCHANGED")
    print("MAX INFERENCE / PARITY: NEXT")

except Exception:
    traceback.print_exc()
    raise SystemExit("PZAAS INPUT CAPTURE: BLOCKED")
PY
