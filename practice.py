cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  -v "$PWD:/workspace:Z" \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -c '
from pathlib import Path
import numpy as np

base = Path("/workspace/artifacts/v1.168-max/cta_max")
for p in sorted(base.rglob("*inv_freq.npy")):
    a = np.load(p)
    print(p.relative_to(base), "SHAPE:", a.shape)

print("EXPECTED:", (128,))
'
