cd /application1/sajjna8/rt-pzaas-v1.0 && \
V="$PWD/artifacts/v1.472-max/pzaas_max/validation" && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm -i --pull=never --network none \
--memory 10g \
--tmpfs /tmp:rw,size=1g \
-e HOME=/tmp \
-e PYTHONDONTWRITEBYTECODE=1 \
-e PYTHONPATH=/validation/sklearn_161:/validation/python_deps:/workspace/artifacts/v1.472/core-artifact:/workspace/artifacts/v1.472/utils/dependency-utils \
-v "$PWD:/workspace:ro" \
-v "$V:/validation:rw" \
-w /workspace \
--entrypoint /opt/venv/bin/python \
localhost/cta-max-faiss:local -u - <<'PY'
import os, sys, types, inspect, traceback
os.umask(0o077)

print("=== PZAAS REAL MODEL FORWARD RETRY ===", flush=True)

try:
    import torch
    import sklearn
    assert sklearn.__version__ == "1.6.1"
    torch.set_num_threads(4)

    ref = torch.load(
        "/validation/ppa_pytorch_reference_01.pt",
        map_location="cpu",
        weights_only=True
    )
    model_in = ref["model_in"]

    keys = [
        "deep_in", "page_in", "item_in",
        "item_meta_in", "page_meta_wide_in",
        "vl_in", "task_in", "ihq_in",
        "jet_name_in", "jet_status_in",
        "sibling_deep_in", "sibling_wide_in",
        "sibling_vl_in", "wide_in",
        "input_ids", "attention_mask"
    ]

    missing = [k for k in keys if k not in model_in]
    print("MISSING INPUTS:", missing, flush=True)
    assert not missing, "Input mapping mismatch"

    kwargs = {
        ("tasks_in" if k == "task_in" else k): model_in[k]
        for k in keys
    }

    print("INPUT MAPPING: PASS", flush=True)

    # Offline-only scheduler substitute.
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

    model = ds.model_base
    model.eval()

    print("FORWARD SIGNATURE:", inspect.signature(model.forward))
    inspect.signature(model.forward).bind(**kwargs)

    print("FORWARD ARGUMENTS: PASS", flush=True)

    with torch.no_grad():
        output = model(**kwargs)

    print("REAL PYTORCH FORWARD: PASS", flush=True)

    def describe(v, name="output"):
        if isinstance(v, torch.Tensor):
            print(name, tuple(v.shape), v.dtype)
            if v.is_floating_point():
                assert bool(torch.isfinite(v).all())
        elif isinstance(v, (list, tuple)):
            print(name, type(v).__name__, len(v))
            for i, x in enumerate(v):
                describe(x, f"{name}[{i}]")
        elif isinstance(v, dict):
            for k, x in v.items():
                describe(x, f"{name}.{k}")
        else:
            print(name, type(v).__name__)

    describe(output)

    path = "/validation/ppa_model_base_reference.pt"
    torch.save(output, path)
    os.chmod(path, 0o600)

    print("PZAAS PYTORCH MODEL REFERENCE: PASS")
    print("ORIGINAL DS: UNCHANGED")
    print("REAL MAX PARITY: NEXT")

except Exception:
    traceback.print_exc()
    raise SystemExit("PZAAS MODEL FORWARD: BLOCKED")
PY
