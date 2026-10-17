podman run --rm --entrypoint /bin/bash \
  -v "$PWD":/workspace:ro -w /workspace \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  -lc 'PYTHONPATH=artifacts/v1.168-max python -u - <<'"'"'PY'"'"'
import numpy as np
from cta_max.run_live_max_inference import infer_max_live

a = np.asarray(infer_max_live(None))
assert a.shape == (1, 2048)
assert np.isfinite(a).all()
print("FIRST MAX INFERENCE: PASS", flush=True)

cached = infer_max_live._max_model
b = np.asarray(infer_max_live(None))
assert infer_max_live._max_model is cached
np.testing.assert_allclose(a, b, rtol=1e-5, atol=1e-5)
print("PERSISTENT MAX CACHE: PASS", flush=True)
PY'
