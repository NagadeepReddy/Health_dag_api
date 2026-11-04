cd /application1/sajjna8/rt-pzaas-v1.0 && \
V="$PWD/artifacts/v1.472-max/pzaas_max/validation" && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm -i --pull=never --network none \
--memory 10g --tmpfs /tmp:rw,size=1g \
-e HOME=/tmp -e PYTHONDONTWRITEBYTECODE=1 \
-e PYTHONPATH=/validation/sklearn_161:/validation/python_deps:/workspace/artifacts/v1.472/core-artifact:/workspace/artifacts/v1.472/utils/dependency-utils \
-v "$PWD:/workspace:ro" -v "$V:/validation:rw" \
-w /workspace \
--entrypoint /opt/venv/bin/python \
localhost/cta-max-faiss:local -u - <<'PY'
import sys, types, inspect, traceback, os
import torch
import numpy as np

print("=== PZAAS REAL FUSION CAPTURE RETRY ===")

torch.set_num_threads(4)
os.umask(0o077)

try:
    # Isolated, inactive scheduler.
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
        def __init__(self, *a, **kw):
            self.jobs = []
        def add_job(self, *a, **kw):
            self.jobs.append((a, kw))
        def get_jobs(self):
            return self.jobs
        def start(self, *a, **kw):
            pass
        def shutdown(self, *a, **kw):
            pass

    class IntervalTrigger:
        def __init__(self, *a, **kw):
            pass

    sys.modules[
        "apscheduler.schedulers.background"
    ].BackgroundScheduler = BackgroundScheduler

    sys.modules[
        "apscheduler.triggers.interval"
    ].IntervalTrigger = IntervalTrigger

    from pipeline import pipeline

    ds = pipeline()
    ds.load()

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

    with torch.no_grad():
        output = model(**kwargs)

    hook.remove()

    fusion = captured["fusion"]
    path = captured["path"]

    assert tuple(fusion.shape) == (1, 8, 256)
    assert tuple(path.shape) == (1, 2048)
    assert tuple(output.shape) == (1, 2048)
    assert torch.isfinite(fusion).all()
    assert torch.isfinite(path).all()

    for name, tensor in (
        ("pzaas_fusion_input.npy", fusion),
        ("pzaas_get_path_input.npy", path)
    ):
        location = "/validation/" + name
        np.save(location, tensor.numpy(), allow_pickle=False)
        os.chmod(location, 0o600)

    print("SCHEDULER ISOLATION: PASS")
    print("ORIGINAL DS FORWARD: PASS")
    print("FUSION:", tuple(fusion.shape))
    print("GET_PATH:", tuple(path.shape))
    print("FUSION CAPTURE: PASS")
    print("ORIGINAL DS: UNCHANGED")
    print("NATIVE MAX PARITY: NEXT")

except Exception:
    traceback.print_exc()
    raise SystemExit("FUSION CAPTURE: BLOCKED")
PY
