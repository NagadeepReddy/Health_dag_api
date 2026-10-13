cd /application/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
from pathlib import Path
import numpy as np

b = Path("artifacts/v1.168-max/cta_max")

fusion = np.load(b / "real_sanity_max_2048_verified_latest.npy")
head = np.load(b / "real_sanity_max_get_path_2048_latest.npy")
ref = np.load(b / "real_sanity_pytorch_same_input_verified.npz")["final"]

assert fusion.shape == head.shape == ref.shape == (1, 2048)

for name, x in [("FUSION", fusion), ("HEAD", head), ("PYTORCH", ref)]:
    print(name, "MAX ABS:", float(np.abs(x).max()))

print("FUSION vs HEAD:", float(np.max(np.abs(fusion-head))))
print("HEAD vs PYTORCH:", float(np.max(np.abs(head-ref))))
print("HEAD MATCH:", bool(np.allclose(head, ref, rtol=1e-3, atol=1e-3)))
PY
