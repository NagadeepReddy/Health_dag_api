podman run --rm -i --entrypoint python \
  -v "$PWD:/workspace:Z" -w /workspace \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys, runpy
import numpy as np
import torch
from pathlib import Path

base = Path("artifacts/v1.168-max/cta_max").resolve()
sys.path.insert(0, str(base))
sys.path.insert(0, str(base.parent))
sys.path.insert(0, "artifacts/v1.168/utils/dependency-utils")

from models import ParallelTransformerBlock, RMSNorm

result = runpy.run_path(
    str(base / "run_real_sanity_max_branch_diag.py"),
    run_name="__main__"
)
outputs = result["outputs"]
assert len(outputs) >= 12, "Current MAX stage outputs missing"

def mx(i):
    return np.asarray(outputs[i].to_numpy(), dtype=np.float32)

real = torch.load(base / "real_sanity_model_in.pt",
                  map_location="cpu", weights_only=True)
state = torch.load(
    "artifacts/v1.168/core-artifact/model_0_base.pt",
    map_location="cpu", weights_only=True
)
state = state.get("state_dict", state)

def w(name):
    return state["sequence_transformer." + name].float()

def make_block(index):
    block = ParallelTransformerBlock(
        dim=256, dim_head=256, heads=2, ff_mult=4
    ).eval()
    prefix = f"sequence_transformer.ptransformer.{index}.fn."
    weights = {
        k[len(prefix):]: v for k, v in state.items()
        if k.startswith(prefix)
    }
    block.load_state_dict(weights, strict=True)
    return block

b0 = make_block(0)
b1 = make_block(1)

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
    x = torch.from_numpy(mx(9).copy())
    pt0 = x + b0(x, real["vl_in"])
    pt1 = pt0 + b1(pt0, real["vl_in"])
    normalized = n1(pt1)
    pooled = torch.cat([
        normalized.mean(1),
        normalized.max(1).values
    ], dim=-1)
    pt_sequence = n2(dense(pooled))

def compare(name, pt, max_value):
    a = pt.detach().numpy()
    b = max_value
    assert a.shape == b.shape, (a.shape, b.shape)
    d = np.abs(a.astype(np.float64) - b.astype(np.float64))
    passed = np.allclose(a, b, rtol=1e-3, atol=1e-3)
    print(name, "PASS" if passed else "FAIL",
          "MAX_DIFF:", float(d.max()),
          "MEAN_DIFF:", float(d.mean()))
    return passed

print("\n=== CURRENT-RUN PYTORCH vs MAX SEQUENCE ===")
checks = [
    compare("BLOCK 0", pt0, mx(10)),
    compare("BLOCK 1", pt1, mx(11)),
    compare("FINAL SEQUENCE", pt_sequence, mx(1)),
]

print("CURRENT SEQUENCE CHECKS:", sum(checks), "/3")
PY
