cd /application1/sajjna8/rt-pzaas-v1.0 && \
mkdir -p artifacts/v1.472-max/pzaas_max/validation && \
chmod 700 artifacts/v1.472-max/pzaas_max/validation && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage run --rm -i \
--network none --memory 10g \
--tmpfs /tmp:rw,size=1g \
-e HOME=/tmp \
-e XDG_CACHE_HOME=/tmp/cache \
-e PYTHONDONTWRITEBYTECODE=1 \
-e PYTHONPATH=/workspace/artifacts/v1.472/core-artifact:/workspace/artifacts/v1.472/utils/dependency-utils \
-v "$PWD:/workspace:ro" \
-v "$PWD/artifacts/v1.472-max/pzaas_max/validation:/validation:rw" \
-w /workspace \
--entrypoint python3 localhost/cta-max-faiss:local -u - <<'PY'
import sys, os, json, traceback
import numpy as np
import torch
from pathlib import Path

os.umask(0o077)
print("=== PZAAS REAL INPUT CAPTURE ===", flush=True)

try:
    from pipeline import pipeline

    ds = pipeline()

    if not getattr(ds, "loaded", False):
        print("LOADING ORIGINAL DS DEPENDENCIES", flush=True)
        ds.load()

    print("ORIGINAL DS LOAD: PASS", flush=True)

    sample = Path(
        "artifacts/v1.472/samples/sanity_input.json"
    )
    body = json.loads(sample.read_text())

    result = ds.preprocess(body)
    model_in = result[0]

    if not isinstance(model_in, dict):
        raise TypeError("Expected model_in dictionary")

    print("ORIGINAL DS PREPROCESS: PASS")
    print("MODEL INPUT FIELDS:", len(model_in))

    arrays = {}
    for name, value in model_in.items():
        if isinstance(value, torch.Tensor):
            array = value.detach().cpu().numpy()
        elif isinstance(value, np.ndarray):
            array = value
        else:
            print("NON-TENSOR FIELD:", name,
                  type(value).__name__)
            continue

        arrays[name] = array
        print("INPUT:", name, array.shape,
              array.dtype, flush=True)

    if not arrays:
        raise RuntimeError("No tensors captured")

    target = "/validation/sanity_model_inputs.npz"
    np.savez_compressed(target, **arrays)

    print("REAL PZAAS INPUT CAPTURE: PASS")
    print("SAVED TENSORS:", len(arrays))
    print("ORIGINAL DS: UNCHANGED")
    print("MAX INFERENCE / PARITY: PENDING")

except Exception:
    traceback.print_exc()
    raise SystemExit("PZAAS INPUT CAPTURE: FAILED")
PY
