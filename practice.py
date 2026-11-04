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
os.umask(0o077)

print("=== PZAAS REAL PYTORCH REFERENCE ===", flush=True)

try:
    import torch
    import sklearn
    assert sklearn.__version__ == "1.6.1"

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

    # Offline validation only; no source-file changes.
    pipeline.schedule_pull = lambda self: None

    ds = pipeline()
    if not getattr(ds, "loaded", False):
        ds.load()

    print("ORIGINAL DS LOAD: PASS", flush=True)

    with open("artifacts/v1.472/samples/ppa_input.json") as f:
        body = json.load(f)

    prepared = ds.preprocess(body)
    assert isinstance(prepared, (tuple, list))
    assert len(prepared) == 7, (
        "Unexpected preprocessing contract",
        len(prepared)
    )

    print("ORIGINAL DS PREPROCESS: PASS", flush=True)

    with torch.no_grad():
        output = ds.inference(*prepared)

    print("REAL PYTORCH INFERENCE: PASS", flush=True)

    target = "/validation/ppa_pytorch_reference.pt"
    torch.save(output, target)
    os.chmod(target, 0o600)

    def describe(value, prefix="output", depth=0):
        if depth > 2:
            return
        if isinstance(value, torch.Tensor):
            print(prefix, tuple(value.shape), value.dtype)
        elif isinstance(value, dict):
            print(prefix, "dict fields:", len(value))
            for k, v in list(value.items())[:20]:
                describe(v, prefix + "." + str(k), depth + 1)
        elif isinstance(value, (tuple, list)):
            print(prefix, type(value).__name__, len(value))
            for i, v in enumerate(value[:8]):
                describe(v, prefix + "." + str(i), depth + 1)
        else:
            print(prefix, type(value).__name__)

    describe(output)

    print("PZAAS PYTORCH REFERENCE: SAVED")
    print("ORIGINAL DS: UNCHANGED")
    print("REAL MAX NUMERICAL PARITY: NEXT")

except Exception:
    traceback.print_exc()
    raise SystemExit("PZAAS PYTORCH REFERENCE: BLOCKED")
PY
