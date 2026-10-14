python - <<'PY'
import torch
import torch.nn.functional as F
import numpy as np
from pathlib import Path

p = Path("artifacts/v1.168-max/cta_max")
real = torch.load(p/"real_sanity_model_in.pt", map_location="cpu", weights_only=True)
state = torch.load("artifacts/v1.168/core-artifact/model_0_base.pt",
                   map_location="cpu", weights_only=True)
state = state.get("state_dict", state)

names = ["page_in", "item_in", "item_meta_in", "page_meta_wide_in"]
missing = [k for k in names if k not in real]
if missing:
    print("INPUT KEYS MISSING:", missing)
    print("AVAILABLE:", list(real.keys()))
    raise SystemExit(0)

prefix = "sequence_transformer."
def weight(name):
    return state[prefix + name].float()

page = F.embedding(torch.as_tensor(real["page_in"]).long(),
                   weight("page_embedding.weight"))
item_ids = torch.as_tensor(real["item_in"]).long()
item = F.embedding(item_ids, weight("item_embedding.weight"))
meta = F.embedding(torch.as_tensor(real["item_meta_in"]).long(),
                   weight("item_meta_embedding.weight"))
pre = F.embedding(item_ids, weight("item_pre_embedding.weight"))

wide = real["page_meta_wide_in"]
if isinstance(wide, (list, tuple)):
    wide = torch.stack([torch.as_tensor(v).float() for v in wide], dim=1)
else:
    wide = torch.as_tensor(wide).float()
    if wide.ndim == 2:
        wide = wide.unsqueeze(-1)
    if wide.shape[1] != weight("page_meta_wide_dense.weight").shape[1]:
        wide = wide.transpose(1, 2)

def features(w):
    pw = F.leaky_relu(F.linear(
        w.transpose(1, 2),
        weight("page_meta_wide_dense.weight"),
        weight("page_meta_wide_dense.bias")), negative_slope=0.2)
    return (torch.cat([page, pw], dim=-1) *
            torch.cat([item, meta, pre], dim=-1)).detach().numpy()

with np.load(p/"max_sequence_stages_diag.npz") as saved:
    actual = saved["features"]

for label, w in [
    ("WITHOUT_BATCHNORM", wide),
    ("WITH_BATCHNORM", F.batch_norm(
        wide,
        weight("page_meta_wide_batch_norm.running_mean"),
        weight("page_meta_wide_batch_norm.running_var"),
        weight("page_meta_wide_batch_norm.weight"),
        weight("page_meta_wide_batch_norm.bias"),
        training=False))
]:
    a = features(w)
    print(label, "SHAPE:", a.shape)
    if a.shape == actual.shape:
        d = np.abs(a.astype(np.float64)-actual.astype(np.float64))
        print("MAX_DIFF:", d.max(), "MEAN_DIFF:", d.mean())
        print("MATCH:", np.allclose(a, actual, rtol=1e-3, atol=1e-3))
    else:
        print("SHAPE MISMATCH vs MAX:", actual.shape)
PY
