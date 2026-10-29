bash <<'SH'
set -euo pipefail

REPO=/application1/sajjna8/rt-pzaas-cta-offers-v1
IMAGE=docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest

test -f "$REPO/artifacts/v1.168/core-artifact/model_0_base.pt"
test -d "$REPO/artifacts/v1.168-max/cta_native_model"

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i \
  --network none \
  --read-only \
  --memory 12g \
  --cpus 2 \
  --pids-limit 64 \
  --tmpfs /tmp:rw,size=512m,mode=1777 \
  -e HOME=/tmp \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -v "$REPO/artifacts/v1.168/core-artifact/model_0_base.pt:/src/model_0_base.pt:ro" \
  -v "$REPO/artifacts/v1.168-max/cta_native_model:/out:rw" \
  --entrypoint /opt/venv/bin/python \
  "$IMAGE" -B - <<'PY'
from pathlib import Path
import torch
from safetensors.torch import save_file
from safetensors import safe_open

src = Path("/src/model_0_base.pt")
dst = Path("/out/cta_real_fp32.safetensors")
tmp = Path("/out/.cta_real_fp32.safetensors.part")

if dst.exists() or tmp.exists():
    raise SystemExit("STOP: Output already exists; nothing overwritten")

state = torch.load(src, map_location="cpu", weights_only=True)
if isinstance(state, dict) and "state_dict" in state:
    state = state["state_dict"]

if not isinstance(state, dict):
    raise SystemExit("STOP: Unexpected checkpoint structure")

weights = {}
for name, value in state.items():
    if isinstance(value, torch.Tensor):
        value = value.detach().cpu()
        if value.is_floating_point():
            value = value.float()
        weights[name] = value.contiguous().clone()

if len(weights) < 100:
    raise SystemExit("STOP: Checkpoint tensor count unexpectedly low")

save_file(weights, str(tmp))
with safe_open(str(tmp), framework="pt", device="cpu") as f:
    count = len(f.keys())

if count != len(weights):
    raise SystemExit("STOP: Safetensors verification failed")

tmp.rename(dst)

print("REAL TRAINED WEIGHTS:", count)
print("FP32 SAFETENSORS: CREATED")
print("OUTPUT:", dst)
print("SIZE BYTES:", dst.stat().st_size)
print("ORIGINAL CHECKPOINT: UNCHANGED")
print("DS CODE: UNCHANGED")
print("MAX SERVER: NOT STARTED")
PY
SH
