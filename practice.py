cd /application/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import torch

p = "artifacts/v1.168-max/cta_max/real_sanity_model_in.pt"
x = torch.load(p, map_location="cpu", weights_only=False)

print("SAVED INPUT TYPE:", type(x).__name__)

if isinstance(x, dict):
    print("INPUT KEYS:", list(x.keys()))
    for name in ("v1_in", "sibling_v1_in"):
        if name in x:
            v = x[name]
            print(name, "=", v.tolist() if hasattr(v, "tolist") else v)
        else:
            print(name, "NOT FOUND AT TOP LEVEL")
else:
    print("INPUT COUNT:", len(x) if hasattr(x, "__len__") else "unknown")
    print("INPUT STRUCTURE:", [type(v).__name__ for v in x] if isinstance(x, (list, tuple)) else "other")
PY
