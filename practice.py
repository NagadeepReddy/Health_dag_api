podman run --rm -i --pull=never \
  -v "$PWD:/workspace:ro" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import torch
import torch.nn.functional as F
import numpy as np
from pathlib import Path

b = Path("artifacts/v1.168-max/cta_max")
s = torch.load("artifacts/v1.168/core-artifact/model_0_base.pt",
               map_location="cpu", weights_only=True)
s = s.get("state_dict", s)
x = torch.load(b/"real_sanity_model_in.pt",
               map_location="cpu", weights_only=True)

def w(name):
    return s["sibling_context_head." + name].float()

def rms(x, name):
    return x * torch.rsqrt(x.square().mean(-1, keepdim=True) + 1e-6) * w(name + ".g")

def linear(x, name):
    key = "sibling_context_head." + name + ".bias"
    return F.linear(x, w(name + ".weight"), s[key].float() if key in s else None)

def swiglu(x, name):
    a = linear(x, name + ".w1")
    c = linear(x, name + ".w3")
    return linear(F.silu(a) * c, name + ".w2")

with torch.no_grad():
    ids = x["sibling_deep_in"][:, :, 0].long()
    wide = x["sibling_wide_in"][:, :, 0].float()

    deep = torch.cat([
        F.embedding(ids[:, i], w(f"deep_embedding.{i}.weight"))
        for i in range(3)
    ], dim=-1)
    deep = swiglu(linear(rms(deep, "deep_norm"), "deep_dense"), "deep_swiglu")

    p = "num_batch_norm"
    wide = F.batch_norm(
        wide, w(p+".running_mean"), w(p+".running_var"),
        w(p+".weight"), w(p+".bias"), training=False, eps=1e-5
    )
    wide = swiglu(linear(rms(wide, "wide_norm"), "wide_dense"), "wide_swiglu")

    result = torch.cat([deep, wide], dim=-1).numpy().ravel()

with np.load(b/"real_sanity_pytorch_same_input_verified.npz") as f:
    saved_pt = f["sibling"].reshape(-1)

with np.load(b/"real_sanity_max_branches.npz") as f:
    saved_max = f["sibling"].reshape(-1)

print("=== DIRECT PYTORCH SIBLING COMPARISON ===")
for name, arr in [
    ("Saved PyTorch", saved_pt[:128]),
    ("Saved MAX", saved_max[:128])
]:
    print(name, "max diff:",
          float(np.max(np.abs(result - arr))))

print("Deep max diff vs saved MAX:",
      float(np.max(np.abs(result[:64] - saved_max[:64]))))
print("Wide max diff vs saved MAX:",
      float(np.max(np.abs(result[64:] - saved_max[64:128]))))
PY
