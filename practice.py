cd /application1/sajjna8/rt-pzaas-v1.0 && \
V="$PWD/artifacts/v1.472-max/pzaas_max/validation" && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm -i --pull=never --network none \
--memory 10g --tmpfs /tmp:rw,size=1g \
-e HOME=/tmp -e PYTHONDONTWRITEBYTECODE=1 \
-e PYTHONPATH=/validation/sklearn_161:/validation/python_deps:/workspace/artifacts/v1.472/core-artifact:/workspace/artifacts/v1.472/utils/dependency-utils \
-v "$PWD:/workspace:ro" \
-v "$V:/validation:rw" \
-w /workspace \
--entrypoint /opt/venv/bin/python \
localhost/cta-max-faiss:local -u - <<'PY'
import sys, types, inspect, traceback, os
import torch
import numpy as np

print("=== PZAAS FUSION CAPTURE ===", flush=True)
torch.set_num_threads(4)
os.umask(0o077)

try:
    # Satisfy imports without starting a scheduler.
    for name in (
        "apscheduler",
        "apscheduler.schedulers",
        "apscheduler.schedulers.background",
        "apscheduler.triggers",
        "apscheduler.triggers.interval"
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

    # Skip ONLY background scheduler initialization.
    # No original DS files are modified.
    pipeline.schedule_pull = lambda self: None

    ds = pipeline()
    ds.load()
    print("ORIGINAL DS LOAD: PASS", flush=True)

    model = ds.model_base
    model.eval()

    ref = torch.load(
        "/validation/ppa_pytorch_reference_01.pt",
        map_location="cpu",
        weights_only=True
    )
    model_in = ref["model_in"]
    captured = {}

    def capture_fusion(module, args):
        captured["fusion"] = args[0].detach().cpu().clone()

    hook = model.moe_norm1.register_forward_pre_hook(
        capture_fusion
    )

    original_get_path = model.get_path

    def capture_path(*args, **kwargs):
        captured["path"] = args[-1].detach().cpu().clone()
        return original_get_path(*args, **kwargs)

    model.get_path = capture_path

    kwargs = {}
    for name in inspect.signature(model.forward).parameters:
        key = "task_in" if name == "tasks_in" else name
        if key in model_in:
            kwargs[name] = model_in[key]

    try:
        with torch.inference_mode():
            output = model(**kwargs)
    finally:
        hook.remove()
        model.get_path = original_get_path

    fusion = captured["fusion"]
    path = captured["path"]

    assert fusion.shape == (1, 8, 256)
    assert path.shape == (1, 2048)
    assert output.shape == (1, 2048)

    for name, value in (
        ("pzaas_fusion_input.npy", fusion),
        ("pzaas_get_path_input.npy", path)
    ):
        file = "/validation/" + name
        np.save(file, value.numpy(), allow_pickle=False)
        os.chmod(file, 0o600)

    print("SCHEDULER BYPASS: PASS")
    print("PYTORCH MODEL FORWARD: PASS")
    print("FUSION INPUT:", tuple(fusion.shape))
    print("PATH INPUT:", tuple(path.shape))
    print("FUSION CAPTURE: PASS")
    print("ORIGINAL DS FILES: UNCHANGED")
    print("REAL MAX PARITY: NEXT")

except Exception:
    traceback.print_exc()
    raise SystemExit("FUSION CAPTURE: BLOCKED")
PY
