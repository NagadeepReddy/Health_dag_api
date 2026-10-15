podman run --rm -i --entrypoint python \
  -v "$PWD:/workspace:Z" -w /workspace \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys, io, runpy, contextlib
from pathlib import Path
import numpy as np
import torch
import torch.nn.functional as F

BASE = Path("artifacts/v1.168-max/cta_max").resolve()
sys.path[:0] = [
    str(BASE), str(BASE.parent),
    str(Path("artifacts/v1.168/utils/dependency-utils").resolve())
]
from models import ParallelTransformerBlock, RMSNorm

print("Running existing MAX graph...", flush=True)
with contextlib.redirect_stdout(io.StringIO()):
    env = runpy.run_path(
        str(BASE / "run_real_sanity_max_branch_diag.py"),
        run_name="__main__"
    )

outputs = env["outputs"]
assert len(outputs) >= 9

x = torch.from_numpy(np.stack([
    np.asarray(o.to_numpy(), dtype=np.float32).reshape(1, 256)
    for o in outputs[1:9]
], axis=1))

state = torch.load(
    "artifacts/v1.168/core-artifact/model_0_base.pt",
    map_location="cpu", weights_only=True
)
state = state.get("state_dict", state)

def substate(prefix):
    return {
        k[len(prefix):]: v for k, v in state.items()
        if k.startswith(prefix)
    }

def linear(x, name, bias=False):
    w = state[name + ".weight"].float()
    b = state[name + ".bias"].float() if bias else None
    return F.linear(x, w, b)

n1 = RMSNorm(256).eval()
n2 = RMSNorm(256).eval()
att = ParallelTransformerBlock(
    dim=256, dim_head=256, heads=1, ff_mult=4
).eval()

n1.load_state_dict(substate("moe_norm1."), strict=True)
n2.load_state_dict(substate("moe_norm2."), strict=True)
att.load_state_dict(substate("att_pooling."), strict=True)

with torch.no_grad():
    z = n2(att(n1(x)))

    # REQUIRED: same flattening as MAX
    z = z.reshape(1, 2048)
    print("FLATTENED SHAPE:", tuple(z.shape))

    z = linear(z, "remove_tasks_dense1", bias=True)

    a = linear(z, "remove_tasks_act1.w1")
    b = linear(z, "remove_tasks_act1.w3")
    z = linear(F.silu(a) * b, "remove_tasks_act1.w2")

    pt_final = z.numpy().astype(np.float32)

max_final = np.asarray(
    outputs[0].to_numpy(), dtype=np.float32
)

assert pt_final.shape == max_final.shape == (1, 2048)

diff = np.abs(
    pt_final.astype(np.float64) -
    max_final.astype(np.float64)
)

print("\n=== COMPLETE FINAL-PATH PARITY ===")
print("PYTORCH SHAPE:", pt_final.shape)
print("MAX SHAPE:", max_final.shape)
print("MAX_DIFF:", float(diff.max()))
print("MEAN_DIFF:", float(diff.mean()))
print("MATCH:", bool(np.allclose(
    pt_final, max_final, rtol=1e-3, atol=1e-3
)))
print("ORIGINAL FILES: UNCHANGED")
PY
