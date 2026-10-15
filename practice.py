podman run --rm -i --entrypoint python \
  -v "$PWD:/workspace:Z" -w /workspace \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys, runpy, contextlib, io
from pathlib import Path
import numpy as np
import torch

BASE = Path("artifacts/v1.168-max/cta_max").resolve()
sys.path[:0] = [
    str(BASE), str(BASE.parent),
    str(Path("artifacts/v1.168/utils/dependency-utils").resolve())
]

from models import ParallelTransformerBlock, RMSNorm

state = torch.load(
    "artifacts/v1.168/core-artifact/model_0_base.pt",
    map_location="cpu", weights_only=True
)
state = state.get("state_dict", state)

def substate(prefix):
    return {
        k[len(prefix):]: v
        for k, v in state.items()
        if k.startswith(prefix)
    }

norm1 = RMSNorm(256).eval()
norm2 = RMSNorm(256).eval()
att = ParallelTransformerBlock(
    dim=256, dim_head=256, heads=1, ff_mult=4
).eval()

norm1.load_state_dict(substate("moe_norm1."), strict=True)
norm2.load_state_dict(substate("moe_norm2."), strict=True)
att.load_state_dict(substate("att_pooling."), strict=True)

print("ORIGINAL PYTORCH FINAL WEIGHTS: PASS", flush=True)
print("Running existing MAX graph...", flush=True)

with contextlib.redirect_stdout(io.StringIO()):
    env = runpy.run_path(
        str(BASE / "run_real_sanity_max_branch_diag.py"),
        run_name="__main__"
    )

outputs = env["outputs"]
assert len(outputs) == 9

max_final = np.asarray(
    outputs[0].to_numpy(), dtype=np.float32
)
assert max_final.shape == (1, 2048)

branches = [
    torch.from_numpy(
        np.asarray(o.to_numpy(), dtype=np.float32).reshape(1, 256)
    )
    for o in outputs[1:]
]

with torch.no_grad():
    x = torch.stack(branches, dim=1)
    x = norm1(x)
    x = att(x)
    x = norm2(x)
    pt_final = x.reshape(1, 2048).numpy()

diff = np.abs(
    pt_final.astype(np.float64) -
    max_final.astype(np.float64)
)

print("\n=== ORIGINAL PYTORCH FINAL STAGE VS MAX ===")
print("PYTORCH SHAPE:", pt_final.shape)
print("MAX SHAPE:", max_final.shape)
print("MAX_DIFF:", float(diff.max()))
print("MEAN_DIFF:", float(diff.mean()))
print("MATCH:", bool(np.allclose(
    pt_final, max_final, rtol=1e-3, atol=1e-3
)))
PY
