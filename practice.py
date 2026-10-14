podman run --rm -i --entrypoint python \
  -v "$PWD:/workspace:Z" -w /workspace \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys, runpy
from pathlib import Path
import numpy as np
import torch
import torch.nn.functional as F

base = Path("artifacts/v1.168-max/cta_max").resolve()
sys.path[:0] = [
    str(base), str(base.parent),
    str(Path("artifacts/v1.168/utils/dependency-utils").resolve())
]
from models import ParallelTransformerBlock, RMSNorm

# Current MAX execution
env = runpy.run_path(
    str(base / "run_real_sanity_max_branch_diag.py"),
    run_name="__main__"
)
outputs = env["outputs"]
assert len(outputs) == 9, f"Expected 9 outputs, got {len(outputs)}"
mx = np.asarray(outputs[1].to_numpy(), dtype=np.float32)

# Independent PyTorch inputs and checkpoint
real = torch.load(
    base / "real_sanity_model_in.pt",
    map_location="cpu", weights_only=True
)
state = torch.load(
    "artifacts/v1.168/core-artifact/model_0_base.pt",
    map_location="cpu", weights_only=True
)
state = state.get("state_dict", state)

def w(name):
    return state["sequence_transformer." + name].float()

def make_block(i):
    block = ParallelTransformerBlock(
        dim=256, dim_head=256, heads=2, ff_mult=4
    ).eval()
    prefix = f"sequence_transformer.ptransformer.{i}.fn."
    block.load_state_dict({
        k[len(prefix):]: v
        for k, v in state.items() if k.startswith(prefix)
    }, strict=True)
    return block

b0, b1 = make_block(0), make_block(1)

n1, n2 = RMSNorm(256).eval(), RMSNorm(256).eval()
dense = torch.nn.Linear(512, 256).eval()

n1.load_state_dict({"g": w("out_norm1.g")})
n2.load_state_dict({"g": w("out_norm2.g")})
dense.load_state_dict({
    "weight": w("seq_dense.weight"),
    "bias": w("seq_dense.bias")
})

with torch.no_grad():
    page = F.embedding(
        real["page_in"].long(), w("page_embedding.weight"))
    item = F.embedding(
        real["item_in"].long(), w("item_embedding.weight"))
    meta = F.embedding(
        real["item_meta_in"].long(), w("item_meta_embedding.weight"))
    pre = F.embedding(
        real["item_in"].long(), w("item_pre_embedding.weight"))

    wide_input = real["page_meta_wide_in"]
    if isinstance(wide_input, (list, tuple)):
        assert len(wide_input) == 1
        wide_input = wide_input[0]
    wide_input = torch.as_tensor(wide_input).float()
    assert wide_input.shape == (1, 50), wide_input.shape
    wide_input = wide_input.unsqueeze(-1)

    wide = F.leaky_relu(
        F.linear(
            wide_input,
            w("page_meta_wide_dense.weight"),
            w("page_meta_wide_dense.bias")
        ),
        negative_slope=0.2
    )

    x = torch.cat([page, wide], dim=-1) * \
        torch.cat([item, meta, pre], dim=-1)

    assert x.shape == (1, 50, 256), x.shape

    x = x + b0(x, real["vl_in"])
    x = x + b1(x, real["vl_in"])
    x = n1(x)
    pooled = torch.cat(
        [x.mean(1), x.max(1).values], dim=-1
    )
    pt = n2(dense(pooled)).numpy()

with np.load(
    base / "real_sanity_pytorch_same_input_verified.npz",
    allow_pickle=False
) as saved:
    old = np.asarray(saved["sequence"], dtype=np.float32)

def compare(label, a, b):
    assert a.shape == b.shape, (label, a.shape, b.shape)
    d = np.abs(a.astype(np.float64) - b.astype(np.float64))
    print(label)
    print("  MAX_DIFF:", float(d.max()))
    print("  MEAN_DIFF:", float(d.mean()))
    print("  MATCH:", bool(np.allclose(
        a, b, rtol=1e-3, atol=1e-3
    )))

print("\n=== INDEPENDENT COMPLETE SEQUENCE CHECK ===")
compare("PYTORCH vs CURRENT MAX", pt, mx)
compare("PYTORCH vs OLD REFERENCE", pt, old)
compare("CURRENT MAX vs OLD REFERENCE", mx, old)
PY
