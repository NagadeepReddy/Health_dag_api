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
import sys, types, json, traceback, os
import numpy as np

os.umask(0o077)

print("=== PZAAS INPUT PREFLIGHT ===", flush=True)

try:
    import torch, sklearn, einops, joblib, cloudpickle
    assert sklearn.__version__ == "1.6.1"

    with open("artifacts/v1.472/samples/sanity_input.json") as f:
        body = json.load(f)

    fixes = 0

    def validate(obj):
        global fixes

        if isinstance(obj, dict):
            page = obj.get("page")

            if isinstance(page, dict):
                name = page.get("name")

                if isinstance(name, str) and \
                   name.lower() == "gridwall_smartphones":

                    value = obj.get("webInteraction_name")

                    if value is None:
                        obj["webInteraction_name"] = ""
                        fixes += 1
                    elif not isinstance(value, str):
                        raise TypeError(
                            "Invalid webInteraction_name type"
                        )

            for value in obj.values():
                validate(value)

        elif isinstance(obj, list):
            for item in obj:
                validate(item)

    validate(body)

    print("INPUT PREFLIGHT: PASS")
    print("TEST-ONLY NULL NORMALIZATIONS:", fixes)

    # Offline scheduler isolation.
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

    pipeline.schedule_pull = lambda self: None

    ds = pipeline()

    if not getattr(ds, "loaded", False):
        ds.load()

    print("ORIGINAL DS LOAD: PASS", flush=True)

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
            print("UNSUPPORTED INPUT:", name, type(value).__name__)

    assert arrays, "No tensors captured"
    assert len(arrays) == len(model_in), \
        "Some inputs require conversion"

    np.savez_compressed(
        "/validation/sanity_model_inputs.npz",
        **arrays
    )

    print("PZAAS MODEL INPUT CAPTURE: PASS")
    print("TENSORS:", len(arrays))
    print("ORIGINAL DS FILES: UNCHANGED")
    print("MAX INFERENCE / PARITY: NEXT")

except Exception:
    traceback.print_exc()
    raise SystemExit("PZAAS INPUT CAPTURE: BLOCKED")
PY
