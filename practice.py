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
print("=== PZAAS ORIGINAL PYTORCH REFERENCE ===", flush=True)

try:
    import torch
    import sklearn
    assert sklearn.__version__ == "1.6.1"

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

    # No source changes; skip background refresh only.
    pipeline.schedule_pull = lambda self: None

    ds = pipeline()
    if not getattr(ds, "loaded", False):
        ds.load()

    print("ORIGINAL DS LOAD: PASS", flush=True)

    with open("artifacts/v1.472/samples/ppa_input.json") as f:
        body = json.load(f)

    # Capture actual DS inference inputs and outputs.
    original_inference = ds.inference
    reference_files = []

    def capture_inference(*args, **kwargs):
        result = original_inference(*args, **kwargs)

        model_in = args[0] if args else kwargs.get("model_in")
        assert model_in is not None, "Inference input missing"

        path = (
            "/validation/ppa_pytorch_reference_"
            f"{len(reference_files) + 1:02d}.pt"
        )

        torch.save({
            "model_in": model_in,
            "output": result
        }, path)

        os.chmod(path, 0o600)
        reference_files.append(path)

        print("PYTORCH INFERENCE: PASS", flush=True)
        print("REFERENCE:", path, flush=True)
        return result

    # Observe inference in memory; preserve its actual result.
    ds.inference = capture_inference

    print("STARTING ORIGINAL DS PREDICT_RAW", flush=True)

    with torch.no_grad():
        response = ds.predict_raw(body)

    print("ORIGINAL DS PREDICT_RAW: PASS", flush=True)
    print("RESPONSE TYPE:", type(response).__name__)
    print("PYTORCH INFERENCE CALLS:", len(reference_files))

    if not reference_files:
        raise RuntimeError(
            "DS returned without invoking PyTorch inference"
        )

    print("PZAAS PYTORCH REFERENCE: PASS")
    print("ORIGINAL DS SOURCE: UNCHANGED")
    print("REAL MAX NUMERICAL PARITY: NEXT")

except Exception:
    traceback.print_exc()
    raise SystemExit("PZAAS PYTORCH REFERENCE: BLOCKED")
PY
