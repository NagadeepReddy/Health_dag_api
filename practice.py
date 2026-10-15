podman run --rm -i --entrypoint python \
  -v "$PWD:/workspace:Z" -w /workspace \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys, re, types, io, contextlib
from pathlib import Path
import numpy as np
import torch

BASE = Path("artifacts/v1.168-max/cta_max").resolve()
sys.path[:0] = [
    str(BASE), str(BASE.parent),
    str(Path("artifacts/v1.168/utils/dependency-utils").resolve())
]

graph_file = BASE / "grecbase_fusion_order_correct_max_branch_diag.py"
runner_file = BASE / "run_real_sanity_max_branch_diag.py"
source = graph_file.read_text()

# Capture the output of the two known normalization calls.
pattern1 = r'''(?m)^([ \t]*)outs\s*=\s*norm\(outs,\s*["']moe_norm1["']\)[ \t]*$'''
pattern2 = r'''(?m)^([ \t]*)outs\s*=\s*norm\(outs,\s*["']moe_norm2["']\)[ \t]*$'''

assert len(re.findall(pattern1, source)) == 1
assert len(re.findall(pattern2, source)) == 1

source = re.sub(
    pattern1,
    lambda m: m.group(0) + "\n" +
              m.group(1) + "diag_norm1 = outs",
    source
)

# The attention result is whatever enters moe_norm2.
source = re.sub(
    pattern2,
    lambda m: m.group(1) + "diag_attention = outs\n" +
              m.group(0) + "\n" +
              m.group(1) + "diag_norm2 = outs",
    source
)

old = (
    "return graph.output(result, seq, context, search0, "
    "search1, task, jet, ihq, sibling)"
)
assert source.count(old) == 1
source = source.replace(
    old,
    old[:-1] +
    ", diag_norm1, diag_attention, diag_norm2)"
)

module_name = "cta_max.grecbase_fusion_order_correct_max_branch_diag"
module = types.ModuleType(module_name)
module.__file__ = str(graph_file)
module.__package__ = "cta_max"
exec(compile(source, str(graph_file), "exec"), module.__dict__)
sys.modules[module_name] = module

runner_source = runner_file.read_text()
runner_source, count = re.subn(
    r"if\s+len\(outputs\)\s*!=\s*9\s*:",
    "if len(outputs) < 9:",
    runner_source
)
assert count == 1

print("Running MAX stage diagnostics...", flush=True)

scope = {
    "__name__": "__main__",
    "__file__": str(runner_file),
    "__package__": None
}

with contextlib.redirect_stdout(io.StringIO()):
    exec(compile(runner_source, str(runner_file), "exec"), scope)

outputs = scope["outputs"]
assert len(outputs) == 12, len(outputs)

from models import ParallelTransformerBlock, RMSNorm

state = torch.load(
    "artifacts/v1.168/core-artifact/model_0_base.pt",
    map_location="cpu",
    weights_only=True
)
state = state.get("state_dict", state)

def weights(prefix):
    return {
        k[len(prefix):]: v
        for k, v in state.items()
        if k.startswith(prefix)
    }

n1 = RMSNorm(256).eval()
n2 = RMSNorm(256).eval()
att = ParallelTransformerBlock(
    dim=256, dim_head=256, heads=1, ff_mult=4
).eval()

n1.load_state_dict(weights("moe_norm1."), strict=True)
n2.load_state_dict(weights("moe_norm2."), strict=True)
att.load_state_dict(weights("att_pooling."), strict=True)

branches = [
    np.asarray(o.to_numpy(), dtype=np.float32).reshape(1, 256)
    for o in outputs[1:9]
]

x = torch.from_numpy(np.stack(branches, axis=1))

with torch.no_grad():
    p1 = n1(x)
    p2 = att(p1)
    p3 = n2(p2)

print("\n=== PYTORCH VS MAX FINAL STAGES ===")

first_failure = None

for name, result, expected in [
    ("MOE_NORM1", outputs[9], p1),
    ("ATTENTION_POOLING", outputs[10], p2),
    ("MOE_NORM2", outputs[11], p3)
]:
    a = np.asarray(result.to_numpy(), dtype=np.float32)
    b = expected.detach().numpy().astype(np.float32)

    assert a.shape == b.shape, (name, a.shape, b.shape)

    diff = np.abs(a.astype(np.float64) - b.astype(np.float64))
    match = np.allclose(a, b, rtol=1e-3, atol=1e-3)

    print(
        name,
        "PASS" if match else "FAIL",
        "MAX_DIFF:", float(diff.max()),
        "MEAN_DIFF:", float(diff.mean())
    )

    if not match and first_failure is None:
        first_failure = name

print("\nFIRST DIFFERENT STAGE:", first_failure or "NONE")
print("ORIGINAL FILES: UNCHANGED")
PY
