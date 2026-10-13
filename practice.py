cd /application/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import torch

x = torch.load(
    "artifacts/v1.168-max/cta_max/real_sanity_model_in.pt",
    map_location="cpu",
    weights_only=False
)

for name in ("vl_in", "sibling_vl_in"):
    v = x.get(name)
    print(name, "=", v.tolist() if hasattr(v, "tolist") else v)
PY
