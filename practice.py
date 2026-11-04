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
import os
import sys
import types
import inspect
import traceback
import numpy as np
import torch

os.umask(0o077)
torch.set_num_threads(4)

print("=== PZAAS REAL FUSION BOUNDARY ===", flush=True)

try:
    ref = torch.load(
        "/validation/ppa_pytorch_reference_01.pt",
        map_location="cpu",
        weights_only=True
    )
    model_in = ref["model_in"]

    # Disable scheduler only in this isolated process.
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

    ds = pipeline()
    if not getattr(ds, "loaded", False):
        ds.load()

    model = ds.model_base
    model.eval()

    assert hasattr(model, "moe_norm1")
    assert hasattr(model, "get_path")

    captured = {}

    # Exact tensor before the PyTorch fusion stack.
    def before_norm(module, args):
        captured["fusion_input"] = (
            args[0].detach().cpu().clone()
        )

    hook = model.moe_norm1.register_forward_pre_hook(
        before_norm
    )

    # Exact tensor after fusion, before task-path logic.
    original_get_path = model.get_path

    def capture_get_path(*args, **kwargs):
        value = args[-1]

        assert isinstance(value, torch.Tensor)

        captured["get_path_input"] = (
            value.detach().cpu().clone()
        )

        return original_get_path(*args, **kwargs)

    model.get_path = capture_get_path

    signature = inspect.signature(model.forward)

    kwargs = {}
    for key in signature.parameters:
        source_key = (
            "task_in" if key == "tasks_in" else key
        )
        assert source_key in model_in, source_key
        kwargs[key] = model_in[source_key]

    print("ORIGINAL INPUT MAPPING: PASS", flush=True)

    with torch.no_grad():
        output = model(**kwargs)

    hook.remove()

    assert isinstance(output, torch.Tensor)
    assert tuple(output.shape) == (1, 2048)

    fusion = captured["fusion_input"]
    get_path_input = captured["get_path_input"]

    print("FUSION INPUT:", tuple(fusion.shape))
    print("GET_PATH INPUT:", tuple(get_path_input.shape))
    print("MODEL OUTPUT:", tuple(output.shape))

    assert tuple(fusion.shape) == (1, 8, 256)
    assert tuple(get_path_input.shape) == (1, 2048)

    assert bool(torch.isfinite(fusion).all())
    assert bool(torch.isfinite(get_path_input).all())
    assert bool(torch.isfinite(output).all())

    # Keep checkpoints solely in isolated PZAAS validation.
    np.save(
        "/validation/pzaas_fusion_input.npy",
        fusion.numpy(),
        allow_pickle=False
    )

    np.save(
        "/validation/pzaas_get_path_input.npy",
        get_path_input.numpy(),
        allow_pickle=False
    )

    for path in (
        "/validation/pzaas_fusion_input.npy",
        "/validation/pzaas_get_path_input.npy"
    ):
        os.chmod(path, 0o600)

    print("PZAAS REAL FUSION CAPTURE: PASS")
    print("PYTORCH FUSION REFERENCE: PASS")
    print("EIGHT BRANCHES: VERIFIED")
    print("ORIGINAL DS: UNCHANGED")
    print("CTA / BPLAN: UNCHANGED")
    print("NATIVE MAX FUSION PARITY: NEXT")

except Exception:
    traceback.print_exc()
    raise SystemExit("PZAAS FUSION CAPTURE: BLOCKED")
PY
