cd /application1/sajjna8/rt-pzaas-v1.0 && \
V="$PWD/artifacts/v1.472-max/pzaas_max/validation" && \
mkdir -p "$V/sklearn_161" && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm -i --pull=never \
--network none --memory 10g \
--tmpfs /tmp:rw,size=1g \
-e HOME=/tmp \
-e PYTHONDONTWRITEBYTECODE=1 \
-e PYTHONPATH=/validation/sklearn_161:/validation/python_deps:/workspace/artifacts/v1.472/core-artifact:/workspace/artifacts/v1.472/utils/dependency-utils \
-v "$PWD:/workspace:ro" \
-v "$V:/validation:rw" \
-v /vzwhome/sajjna8:/wheels:ro \
-w /workspace \
--entrypoint /bin/sh \
localhost/cta-max-faiss:local -ec '
set -- /wheels/scikit_learn-1.6.1-*.whl
test -f "$1" || {
  echo "SKLEARN 1.6.1 WHEEL MISSING"
  exit 2
}

/opt/venv/bin/python -m pip install \
  --no-index --no-deps --no-compile \
  --target /validation/sklearn_161 "$1"

/opt/venv/bin/python -u -' <<'PY'
import sys, types, json, traceback, os
import numpy as np

os.umask(0o077)

print("=== PZAAS REAL INPUT CAPTURE RETRY ===", flush=True)

try:
    import sklearn
    assert sklearn.__version__ == "1.6.1", sklearn.__version__
    print("SCIKIT-LEARN:", sklearn.__version__, "PASS", flush=True)

    import torch, einops, joblib, cloudpickle, scipy, threadpoolctl
    print("DS DEPENDENCIES: PASS", flush=True)

    # Offline test only: no background refresh.
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

    class IntervalTrigger:
        def __init__(self, *a, **kw): pass

    sys.modules[
        "apscheduler.schedulers.background"
    ].BackgroundScheduler = BackgroundScheduler

    sys.modules[
        "apscheduler.triggers.interval"
    ].IntervalTrigger = IntervalTrigger

    from pipeline import pipeline

    # Do not edit original DS source files.
    pipeline.schedule_pull = lambda self: None

    print("DS IMPORT: PASS", flush=True)

    ds = pipeline()
    if not getattr(ds, "loaded", False):
        ds.load()

    print("ORIGINAL DS LOAD: PASS", flush=True)

    with open("artifacts/v1.472/samples/sanity_input.json") as f:
        body = json.load(f)

    result = ds.preprocess(body)
    model_in = result[0]

    assert isinstance(model_in, dict)

    print("REAL DS PREPROCESS: PASS", flush=True)

    arrays = {}
    for name, value in model_in.items():
        if isinstance(value, torch.Tensor):
            value = value.detach().cpu().numpy()

        if isinstance(value, np.ndarray):
            arrays[name] = value
            print("INPUT:", name, value.shape, value.dtype)
        else:
            print("NON-ARRAY:", name, type(value).__name__)

    assert arrays, "No model tensors captured"
    assert len(arrays) == len(model_in), "Some inputs need conversion"

    np.savez_compressed(
        "/validation/sanity_model_inputs.npz",
        **arrays
    )

    print("PZAAS REAL INPUT CAPTURE: PASS")
    print("CAPTURED TENSORS:", len(arrays))
    print("ORIGINAL DS FILES: UNCHANGED")
    print("REAL MAX INFERENCE / PARITY: NEXT")

except Exception:
    traceback.print_exc()
    raise SystemExit("PZAAS INPUT CAPTURE: BLOCKED")
PY
