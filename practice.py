podman run --rm -i --entrypoint python \
  -v "$PWD:/workspace:Z" -w /workspace \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys, io, re, contextlib
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

runner = BASE / "run_real_sanity_max_branch_diag.py"
source = runner.read_text()

pattern = (
    r"(?m)^([ \t]*)actual\s*=\s*"
    r"actual\.reshape\(expected\.shape\)[ \t]*$"
)

source, count = re.subn(
    pattern,
    lambda m: (
        m.group(1) +
        "pt_refs[name] = np.asarray(expected, dtype=np.float32).copy()\n"
        + m.group(0)
    ),
    source
)
assert count == 1, f"Reference capture locations: {count}"

scope = {
    "__name__": "__main__",
    "__file__": str(runner),
    "__package__": None,
    "pt_refs": {}
}

print("Running existing MAX graph and capturing PyTorch references...",
      flush=True)

with contextlib.redirect_stdout(io.StringIO()) as log:
    exec(compile(source, str(runner), "exec"), scope)

for line in log.getvalue().splitlines():
    if "CURRENT BRANCH PARITY:" in line:
        print(line)

names = [
    "sequence", "context", "search0", "search1",
    "task", "jet", "ihq", "sibling"
]

refs = scope["pt_refs"]
assert set(refs) == set(names), list(refs)

# Important: independent PyTorch references, not MAX branch outputs.
x = torch.from_numpy(np.stack([
    refs[name].reshape(1, 256)
    for name in names
], axis=1))

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

def linear(value, name, bias=False):
    w = state[name + ".weight"].float()
    b = state[name + ".bias"].float() if bias else None
    return F.linear(value, w, b)

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
    z = z.reshape(1, 2048)

    z = linear(z, "remove_tasks_dense1", bias=True)

    a = linear(z, "remove_tasks_act1.w1")
    b = linear(z, "remove_tasks_act1.w3")
    z = linear(F.silu(a) * b, "remove_tasks_act1.w2")

    pt_final = z.numpy().astype(np.float32)

max_final = np.asarray(
    scope["outputs"][0].to_numpy(), dtype=np.float32
)

assert pt_final.shape == max_final.shape == (1, 2048)

diff = np.abs(
    pt_final.astype(np.float64) -
    max_final.astype(np.float64)
)

print("\n=== INDEPENDENT FULL-MODEL PARITY ===")
print("PYTORCH SHAPE:", pt_final.shape)
print("MAX SHAPE:", max_final.shape)
print("MAX_DIFF:", float(diff.max()))
print("MEAN_DIFF:", float(diff.mean()))
print("MATCH:", bool(np.allclose(
    pt_final, max_final, rtol=1e-3, atol=1e-3
)))
print("ORIGINAL FILES: UNCHANGED")
PY
