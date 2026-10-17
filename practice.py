podman run --rm --entrypoint /bin/bash \
  -v "$PWD":/workspace:ro -w /workspace \
  docker-remote.oneartifactoryci.verizon.com/modular/max-nvidia-full:latest \
  -lc 'PYTHONPATH=artifacts/v1.168-max python - <<'"'"'PY'"'"'
import numpy as np
from cta_max.run_live_max_inference import infer_max_live

print("FIRST MAX INFERENCE", flush=True)
a = np.array(infer_max_live(None), copy=True)
cached_model = infer_max_live._max_model

print("SECOND MAX INFERENCE", flush=True)
b = infer_max_live(None)

assert infer_max_live._max_model is cached_model, "Model cache not reused"
np.testing.assert_allclose(a, b, rtol=1e-5, atol=1e-5)
print("PASS: Native MAX inference and cached model reuse", flush=True)
PY'
