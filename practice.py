cd /application/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
from pathlib import Path
import numpy as np

base = Path("artifacts/v1.168-max/cta_max/get_path_weights")

for name in (
    "remove_tasks_dense1.weight",
    "remove_tasks_dense1.bias",
    "remove_tasks_act1.w1.weight",
    "remove_tasks_act1.w3.weight",
    "remove_tasks_act1.w2.weight",
):
    p = base / (name + ".npy")
    print(name, np.load(p, mmap_mode="r").shape if p.exists() else "MISSING")
PY
