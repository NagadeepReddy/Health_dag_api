podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  - <<'PY'
import torch

ckpt = torch.load(
    "artifacts/v1.168/core-artifact/model_0_base.pt",
    map_location="cpu",
    weights_only=False
)

for name, tensor in ckpt.items():
    if name.startswith("sequence_transformer.") and ".ptransformer." not in name:
        print(name, tuple(tensor.shape))
PY
