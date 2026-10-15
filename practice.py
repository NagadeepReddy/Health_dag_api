podman run --rm -i --entrypoint python \
  -v "$PWD:/workspace:Z" -w /workspace \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys
import tempfile
from pathlib import Path
import numpy as np
import torch
import torch.nn.functional as F

BASE = Path("artifacts/v1.168-max/cta_max").resolve()
sys.path[:0] = [
    str(BASE),
    str(BASE.parent),
    str(Path("artifacts/v1.168/utils/dependency-utils").resolve())
]

from models import ParallelTransformerBlock, RMSNorm

real = torch.load(
    BASE / "real_sanity_model_in.pt",
    map_location="cpu",
    weights_only=True
)

state = torch.load(
    "artifacts/v1.168/core-artifact/model_0_base.pt",
    map_location="cpu",
    weights_only=True
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
        for k, v in state.items()
        if k.startswith(prefix)
    }, strict=True)
    return block

b0, b1 = make_block(0), make_block(1)

n1 = RMSNorm(256).eval()
n2 = RMSNorm(256).eval()
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

    wide = real["page_meta_wide_in"]
    if isinstance(wide, (list, tuple)):
        assert len(wide) == 1
        wide = wide[0]

    wide = torch.as_tensor(wide).float()
    assert wide.shape == (1, 50), wide.shape

    wide = F.leaky_relu(
        F.linear(
            wide.unsqueeze(-1),
            w("page_meta_wide_dense.weight"),
            w("page_meta_wide_dense.bias")
        ),
        negative_slope=0.2
    )

    x = torch.cat([page, wide], dim=-1) * \
        torch.cat([item, meta, pre], dim=-1)

    assert x.shape == (1, 50, 256)

    x = x + b0(x, real["vl_in"])
    x = x + b1(x, real["vl_in"])
    x = n1(x)

    pooled = torch.cat(
        [x.mean(1), x.max(1).values], dim=-1
    )
    pt_sequence = n2(dense(pooled)).numpy().astype(np.float32)

assert pt_sequence.shape == (1, 256)

original_ref = BASE / "real_sanity_pytorch_same_input_verified.npz"
runner = BASE / "run_real_sanity_max_branch_diag.py"

with np.load(original_ref, allow_pickle=False) as old:
    refs = {k: old[k].copy() for k in old.files}

assert "sequence" in refs
assert refs["sequence"].shape == pt_sequence.shape
refs["sequence"] = pt_sequence

with tempfile.TemporaryDirectory() as tmp:
    fresh_ref = Path(tmp) / "fresh_pytorch_reference.npz"
    np.savez(fresh_ref, **refs)

    source = runner.read_text()
    old_name = "real_sanity_pytorch_same_input_verified.npz"

    assert old_name in source, "STOP: Reference location changed"

    source = source.replace(old_name, str(fresh_ref))

    print("=== FRESH PYTORCH EIGHT-BRANCH VALIDATION ===", flush=True)
    print("Original checkpoint: unchanged")
    print("MAX code: unchanged")
    print("Old reference: unchanged")
    print("Sequence reference: independently rebuilt from PyTorch",
          flush=True)

    scope = {
        "__name__": "__main__",
        "__file__": str(runner),
        "__package__": None
    }
    exec(compile(source, str(runner), "exec"), scope)
PY
