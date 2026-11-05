
cd /application1/sajjna8/rt-pzaas-v1.0 && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage run --rm -i \
--network none \
--security-opt label=disable \
-v "$PWD:/workspace:ro" \
-w /workspace \
-e PYTHONPATH="/workspace/artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev:/workspace/artifacts/v1.472-max/maxserve_pzaas_extension:/workspace/artifacts/v1.472-max:/workspace/artifacts/v1.472-max/pzaas_max:/workspace/artifacts/v1.472/core-artifact:/workspace/artifacts/v1.472/utils/dependency-utils" \
--entrypoint /opt/venv/bin/python \
localhost/cta-max-faiss:local - <<'PY'
import traceback
from pathlib import Path
import numpy as np

print("=== PZAAS REAL MAX BRIDGE EXECUTION ===", flush=True)

try:
    import torch
    from pzaas_max_model_adapter import PZAASMAXModel

    root = Path("/workspace/artifacts/v1.472-max")
    sources = list(root.rglob("ppa_model_input_exact.pt"))
    if len(sources) != 1:
        raise RuntimeError(
            f"Expected one exact input artifact; found {len(sources)}"
        )

    saved = torch.load(
        sources[0],
        map_location="cpu",
        weights_only=False
    )

    model_in = saved.get("model_in", saved)
    if not isinstance(model_in, dict):
        raise TypeError("Saved model input is not a dictionary")

    print("SAVED INPUT: PASS", flush=True)

    model = PZAASMAXModel()
    print("MODEL INITIALIZATION: PASS", flush=True)

    output = model(model_in)

    if isinstance(output, torch.Tensor):
        result = output.detach().cpu().numpy()
    elif hasattr(output, "to_numpy"):
        result = output.to_numpy()
    else:
        result = np.asarray(output)

    print("OUTPUT SHAPE:", result.shape, flush=True)

    if result.shape != (1, 2048):
        raise RuntimeError("Unexpected PZAAS output shape")

    if not np.isfinite(result).all():
        raise RuntimeError("Non-finite MAX output")

    print("PZAAS REAL MAX BRIDGE FORWARD: PASS")
    print("NEXT: CONNECT BRIDGE TO NATIVE WORKER")

except Exception:
    print("BRIDGE FORWARD: BLOCKED")
    traceback.print_exc()
    raise SystemExit(1)

finally:
    print("ORIGINAL DS: UNCHANGED")
    print("CTA / BPLAN: UNCHANGED")
    print("SOURCE FILES MODIFIED: NONE")
PY
