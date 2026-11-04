cd /application1/sajjna8/rt-pzaas-v1.0 && \
V="$PWD/artifacts/v1.472-max/pzaas_max/validation" && \
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
-w /workspace \
--entrypoint /opt/venv/bin/python \
localhost/cta-max-faiss:local -u - <<'PY'
import sys, types, json, os, traceback
import numpy as np

os.umask(0o077)

print("=== PZAAS REAL INPUT CAPTURE ===", flush=True)

try:
    import torch, sklearn
    assert sklearn.__version__ == "1.6.1"

    # Disable only background scheduling for offline validation.
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

    class IntervalTrigger:
        def __init__(self, *a, **k): pass

    sys.modules[
        "apscheduler.schedulers.background"
    ].BackgroundScheduler = BackgroundScheduler
    sys.modules[
        "apscheduler.triggers.interval"
    ].IntervalTrigger = IntervalTrigger

    from pipeline import pipeline
    pipeline.schedule_pull = lambda self: None

    ds = pipeline()
    if not getattr(ds, "loaded", False):
        ds.load()

    print("ORIGINAL DS LOAD: PASS", flush=True)

    path = "artifacts/v1.472/samples/ppa_input.json"
    with open(path) as f:
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
        else:
            print("NON-TENSOR:", name, type(value).__name__)

    assert arrays, "No model tensors captured"
    assert len(arrays) == len(model_in), "Incomplete capture"

    np.savez_compressed(
        "/validation/ppa_model_inputs.npz",
        **arrays
    )

    print("PZAAS REAL INPUT CAPTURE: PASS")
    print("CAPTURED TENSORS:", len(arrays))
    print("ORIGINAL DS: UNCHANGED")
    print("REAL MAX INFERENCE: NEXT")

except Exception:
    traceback.print_exc()
    raise SystemExit("INPUT CAPTURE: BLOCKED")
PY
