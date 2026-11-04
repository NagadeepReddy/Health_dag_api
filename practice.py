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
set -- /wheels/threadpoolctl-*.whl
test -f "$1" || { echo "THREADPOOLCTL WHEEL MISSING"; exit 2; }

/opt/venv/bin/python -m pip install \
  --no-index --no-deps --no-cache-dir \
  --target /validation/python_deps "$1"

if ! /opt/venv/bin/python -c "import scipy; import scipy.special" >/dev/null 2>&1; then
  set -- /wheels/scipy-*.whl
  test -f "$1" || { echo "SCIPY WHEEL MISSING"; exit 2; }

  /opt/venv/bin/python -m pip install \
    --no-index --no-deps --no-cache-dir \
    --target /validation/python_deps "$1"
fi

/opt/venv/bin/python -u -' <<'PY'
import sys, types, os, json, traceback
import numpy as np

os.umask(0o077)

print("=== PZAAS RUNTIME VALIDATION ===", flush=True)

try:
    import torch, einops, joblib, sklearn
    import cloudpickle, threadpoolctl, scipy

    print("PZAAS RUNTIME DEPENDENCIES: PASS", flush=True)

    # Offline validation only; no DS files modified.
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

    model_in = ds.preprocess(body)[0]
    assert isinstance(model_in, dict)

    arrays = {}

    for name, value in model_in.items():
        if isinstance(value, torch.Tensor):
            value = value.detach().cpu().numpy()
        if isinstance(value, np.ndarray):
            arrays[name] = value
            print("INPUT:", name, value.shape, value.dtype)

    assert len(arrays) == len(model_in), \
        "Some model inputs were not captured"

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
