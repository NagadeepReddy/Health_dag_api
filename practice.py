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

print("=== PZAAS EXACT DS INPUT CAPTURE ===", flush=True)

try:
    import torch
    import sklearn
    assert sklearn.__version__ == "1.6.1"

    # Offline validation: no background scheduler.
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

    with open("artifacts/v1.472/samples/ppa_input.json") as f:
        body = json.load(f)

    result = ds.preprocess(body)
    model_in = result[0]

    assert isinstance(model_in, dict)

    print("ORIGINAL DS PREPROCESS: PASS", flush=True)

    # Preserve exact tensors, lists, strings and dtypes.
    target = "/validation/ppa_model_input_exact.pt"
    torch.save(model_in, target)

    arrays = {}

    for name, value in model_in.items():
        if isinstance(value, torch.Tensor):
            arrays[name] = value.detach().cpu().numpy()
            print("TENSOR:", name, tuple(value.shape), value.dtype)
        else:
            print("PRESERVED:", name, type(value).__name__)

    np.savez_compressed(
        "/validation/ppa_tensor_inputs.npz",
        **arrays
    )

    # Verify the exact saved structure.
    restored = torch.load(
        target, map_location="cpu", weights_only=True
    )

    assert restored.keys() == model_in.keys()

    print("PZAAS EXACT INPUT CAPTURE: PASS")
    print("TOTAL FIELDS:", len(model_in))
    print("NUMERIC TENSOR FIELDS:", len(arrays))
    print("OTHER FIELDS:", len(model_in) - len(arrays))
    print("ORIGINAL DS FILES: UNCHANGED")
    print("REAL MAX INFERENCE / PARITY: NEXT")

except Exception:
    traceback.print_exc()
    raise SystemExit("PZAAS INPUT CAPTURE: BLOCKED")
PY
