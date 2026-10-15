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

def capture(pattern, name):
    global source
    regex = re.compile(
        r"(?m)^([ \t]*)" + pattern + r"[ \t]*$"
    )
    matches = list(regex.finditer(source))
    if len(matches) != 1:
        raise RuntimeError(
            f"STOP: Cannot uniquely locate {name}: {len(matches)}"
        )
    m = matches[0]
    source = (
        source[:m.end()] +
        "\n" + m.group(1) + name + " = outs" +
        source[m.end():]
    )

capture(r"""outs\s*=\s*norm\(outs,\s*["']moe_norm1["']\)""",
        "diag_norm1")
capture(r"outs\s*=\s*block\(outs\)", "diag_attention")
capture(r"""outs\s*=\s*norm\(outs,\s*["']moe_norm2["']\)""",
        "diag_norm2")

old = (
    "return graph.output(result, seq, context, search0, "
    "search1, task, jet, ihq, sibling)"
)
assert source.count(old) == 1, "STOP: Graph output differs"
source = source.replace(
    old,
    old[:-1] + ", diag_norm1, diag_attention, diag_norm2)"
)

# Replace the graph module in memory only.
import cta_max
module_name = "cta_max.grecbase_fusion_order_correct_max_branch_diag"
module = types.ModuleType(module_name)
module.__file__ = str(graph_file)
module.__package__ = "cta_max"
exec(compile(source, str(graph_file), "exec"), module.__dict__)
sys.modules[module_name] = module

# Existing runner, allowing the three additional diagnostic outputs.
runner_source = runner_file.read_text()
runner_source, count = re.subn(
    r"if\s+len\(outputs\)\s*!=\s*9\s*:",
    "if len(outputs) < 9:",
    runner_source
)
assert count == 1, "STOP: Runner output check changed"

print("Running existing MAX graph with stage diagnostics...",
      flush=True)

scope = {
    "__name__": "__main__",
    "__file__": str(runner_file),
    "__package__": None
}
with contextlib.redirect_stdout(io.StringIO()):
    exec(compile(runner_source, str(runner_file), "exec"), scope)

outputs = scope["outputs"]
assert len(outputs) == 12, f"Expected 12, got {len(outputs)}"

# Same eight MAX branch outputs for both implementations.
parts = [
    np.asarray(o.to_numpy(), dtype=np.float32).reshape(1, 256)
    for o in outputs[1:9]
]
x = torch.from_numpy(np.stack(parts, axis=1))

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

with torch.no_grad():
    pt_norm1 = norm1(x)
    pt_attention = att(pt_norm1)
    pt_norm2 = norm2(pt_attention)

checks = [
    ("MOE_NORM1", outputs[9], pt_norm1),
    ("ATTENTION_POOLING", outputs[10], pt_attention),
    ("MOE_NORM2", outputs[11], pt_norm2)
]

print("\n=== FINAL STAGE-BY-STAGE PYTORCH VS MAX ===")
first_failure = None

for name, max_output, pt_output in checks:
    a = np.asarray(max_output.to_numpy(), dtype=np.float32)
    b = pt_output.detach().numpy().astype(np.float32)
    assert a.shape == b.shape, (name, a.shape, b.shape)

    d = np.abs(a.astype(np.float64) - b.astype(np.float64))
    match = bool(np.allclose(a, b, rtol=1e-3, atol=1e-3))

    print(name, "PASS" if match else "FAIL",
          "MAX_DIFF:", float(d.max()),
          "MEAN_DIFF:", float(d.mean()))

    if not match and first_failure is None:
        first_failure = name

actual_final = np.asarray(outputs[0].to_numpy())
last_stage = np.asarray(outputs[11].to_numpy()).reshape(1, 2048)
assert np.allclose(actual_final, last_stage, atol=1e-5), \
    "Diagnostic stages do not reproduce MAX final output"

print("\nFIRST DIFFERENT STAGE:",
      first_failure or "ALL THREE PASS")
print("ORIGINAL FILES: UNCHANGED")
PY
