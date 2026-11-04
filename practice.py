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
import os, sys, types, traceback, inspect

os.umask(0o077)

print("=== PZAAS ORIGINAL MODEL FORWARD ===", flush=True)

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

    # Offline scheduler isolation only.
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

    model = ds.model_base
    model.eval()

    keys = [
        "deep_in",
        "page_in",
        "item_in",
        "item_meta_in",
        "page_meta_wide_in",
        "v1_in",
        "task_in",
        "ihq_in",
        "jet_name_in",
        "jet_status_in",
        "sibling_deep_in",
        "sibling_wide_in",
        "sibling_v1_in",
        "wide_in",
        "input_ids",
        "attention_mask",
    ]

    assert all(k in model_in for k in keys)

    kwargs = {
        ("tasks_in" if k == "task_in" else k): model_in[k]
        for k in keys
    }

    print("MODEL ARGUMENTS:", len(kwargs), flush=True)
    print("FORWARD SIGNATURE:",
          inspect.signature(model.forward), flush=True)

    with torch.no_grad():
        output = model(**kwargs)

    print("ORIGINAL PYTORCH MODEL FORWARD: PASS", flush=True)

    tensors = []

    def collect(value):
        if isinstance(value, torch.Tensor):
            tensors.append(value)
        elif isinstance(value, dict):
            for v in value.values():
                collect(v)
        elif isinstance(value, (list, tuple)):
            for v in value:
                collect(v)

    collect(output)

    print("OUTPUT TENSORS:", len(tensors))

    assert tensors, "Model returned no tensors"

    for i, value in enumerate(tensors):
        print(
            "OUTPUT", i,
            "SHAPE:", tuple(value.shape),
            "DTYPE:", value.dtype,
            "FINITE:",
            bool(torch.isfinite(value).all())
            if value.is_floating_point() else "N/A"
        )

    target = "/validation/ppa_model_base_reference.pt"

    torch.save(output, target)
    os.chmod(target, 0o600)

    print("PZAAS MODEL BASE REFERENCE: PASS")
    print("PYTORCH REFERENCE: SAVED")
    print("ORIGINAL DS: UNCHANGED")
    print("PZAAS MAX GRAPH ALIGNMENT: NEXT")

except Exception:
    traceback.print_exc()
    raise SystemExit("PZAAS MODEL BASE FORWARD: BLOCKED")
PY
