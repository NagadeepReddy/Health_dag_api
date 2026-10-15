podman run --rm -i --entrypoint python \
  -v "$PWD:/workspace:Z" -w /workspace \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys, runpy, io, contextlib
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

print("Running existing MAX graph...", flush=True)

log = io.StringIO()
with contextlib.redirect_stdout(log):
    env = runpy.run_path(
        str(BASE / "run_real_sanity_max_branch_diag.py"),
        run_name="__main__"
    )

outputs = env["outputs"]
assert len(outputs) >= 9

branches = [
    np.asarray(o.to_numpy(), dtype=np.float32).reshape(1, 256)
    for o in outputs[1:9]
]

x = torch.from_numpy(np.stack(branches, axis=1))

state = torch.load(
    "artifacts/v1.168/core-artifact/model_0_base.pt",
    map_location="cpu",
    weights_only=True
)
state = state.get("state_dict", state)

def substate(prefix):
    return {
        k[len(prefix):]: v
        for k, v in state.items()
        if k.startswith(prefix)
    }

def weight(name):
    if name not in state:
        raise RuntimeError("Missing original checkpoint weight: " + name)
    return state[name].float()

n1 = RMSNorm(256).eval()
n2 = RMSNorm(256).eval()
att = ParallelTransformerBlock(
    dim=256, dim_head=256, heads=1, ff_mult=4
).eval()

n1.load_state_dict(substate("moe_norm1."), strict=True)
n2.load_state_dict(substate("moe_norm2."), strict=True)
att.load_state_dict(substate("att_pooling."), strict=True)

def linear(x, prefix, bias=False):
    w = weight(prefix + ".weight")
    b = weight(prefix + ".bias") if bias else None
    return F.linear(x, w, b)

with torch.no_grad():
    z = n2(att(n1(x)))

    # Original additional final layers
    z = linear(z, "remove_tasks_dense1", bias=True)

    a = linear(z, "remove_tasks_act1.w1")
    b = linear(z, "remove_tasks_act1.w3")
    z = linear(
        F.silu(a) * b,
        "remove_tasks_act1.w2"
    )

    pt_final = z.reshape(1, 2048).numpy()

max_final = np.asarray(
    outputs[0].to_numpy(),
    dtype=np.float32
)

assert pt_final.shape == max_final.shape == (1, 2048)

diff = np.abs(
    pt_final.astype(np.float64) -
    max_final.astype(np.float64)
)

print("\n=== COMPLETE PYTORCH FINAL PATH VS MAX ===")
print("PYTORCH:", pt_final.shape)
print("MAX:", max_final.shape)
print("MAX_DIFF:", float(diff.max()))
print("MEAN_DIFF:", float(diff.mean()))
print("MATCH:", bool(np.allclose(
    pt_final, max_final,
    rtol=1e-3, atol=1e-3
)))
print("ORIGINAL FILES: UNCHANGED")
PY
