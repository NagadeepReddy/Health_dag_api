cd /application/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import numpy as np
from pathlib import Path

base = Path("artifacts/v1.168-max/cta_max")

pt = np.load(
    base / "real_sanity_pytorch_same_input_verified.npz"
)["final"].reshape(-1)

mx = np.load(
    base / "real_sanity_max_2048_full_runner.npy"
).reshape(-1)

assert pt.shape == mx.shape == (2048,), "STOP: Shape mismatch"

diff = np.abs(pt - mx)

print("FULL MAX DIFF:", float(diff.max()))
print("MEAN DIFF:", float(diff.mean()))

print("\nERROR BY 256-FEATURE REGION:")
for i in range(8):
    d = diff[i*256:(i+1)*256]
    print(i, "max =", float(d.max()),
          "mean =", float(d.mean()))

print("\nTOP 10 DIFFERENCES:")
for idx in np.argsort(diff)[-10:][::-1]:
    print(int(idx), "PT =", float(pt[idx]),
          "MAX =", float(mx[idx]),
          "DIFF =", float(diff[idx]))
PY
