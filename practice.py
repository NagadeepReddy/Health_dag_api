podman run --rm -i --entrypoint python \
  -v "$PWD:/workspace:Z" -w /workspace \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import torch
import torch.nn.functional as F
import numpy as np
from pathlib import Path

p = Path("artifacts/v1.168-max/cta_max")

real = torch.load(p / "real_sanity_model_in.pt",
                  map_location="cpu", weights_only=True)
state = torch.load("artifacts/v1.168/core-artifact/model_0_base.pt",
                   map_location="cpu", weights_only=True)
state = state.get("state_dict", state)

def w(name):
    return state["sequence_transformer." + name].float()

page_ids = real["page_in"].long()
item_ids = real["item_in"].long()
meta_ids = real["item_meta_in"].long()

page = F.embedding(page_ids, w("page_embedding.weight"))
item = F.embedding(item_ids, w("item_embedding.weight"))
meta = F.embedding(meta_ids, w("item_meta_embedding.weight"))
pre = F.embedding(item_ids, w("item_pre_embedding.weight"))

wide = torch.as_tensor(real["page_meta_wide_in"][0]).float()
wide = wide.reshape(1, 50, 1)

page_wide = F.leaky_relu(
    F.linear(wide, w("page_meta_wide_dense.weight"),
             w("page_meta_wide_dense.bias")),
    negative_slope=0.2
)

pt_features = (
    torch.cat([page, page_wide], dim=-1) *
    torch.cat([item, meta, pre], dim=-1)
).detach().numpy()

with np.load(p / "max_sequence_stages_diag.npz") as data:
    mx_features = data["features"]

print("PYTORCH:", pt_features.shape)
print("MAX:", mx_features.shape)

assert pt_features.shape == mx_features.shape
diff = np.abs(pt_features.astype(np.float64) -
              mx_features.astype(np.float64))

print("MAX_DIFF:", diff.max())
print("MEAN_DIFF:", diff.mean())
print("MATCH:", np.allclose(
    pt_features, mx_features, rtol=1e-3, atol=1e-3))
PY
