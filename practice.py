podman run --rm -i --entrypoint python \
  -v "$PWD:/workspace:Z" -w /workspace \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import ast
import sys
import types
import re
import io
import contextlib
from pathlib import Path
import numpy as np
import torch

BASE = Path("artifacts/v1.168-max/cta_max").resolve()
sys.path[:0] = [
    str(BASE),
    str(BASE.parent),
    str(Path("artifacts/v1.168/utils/dependency-utils").resolve())
]

graph_file = BASE / "grecbase_fusion_order_correct_max_branch_diag.py"
runner_file = BASE / "run_real_sanity_max_branch_diag.py"

class CaptureStages(ast.NodeTransformer):
    def __init__(self):
        self.found = {"moe_norm1": 0, "moe_norm2": 0, "output": 0}

    def assign(self, name):
        return ast.Assign(
            targets=[ast.Name(id=name, ctx=ast.Store())],
            value=ast.Name(id="outs", ctx=ast.Load())
        )

    def visit_Assign(self, node):
        self.generic_visit(node)

        if not (
            len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "outs"
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "norm"
            and len(node.value.args) >= 2
            and isinstance(node.value.args[1], ast.Constant)
        ):
            return node

        name = node.value.args[1].value

        if name == "moe_norm1":
            self.found[name] += 1
            return [node, self.assign("diag_norm1")]

        if name == "moe_norm2":
            self.found[name] += 1
            return [
                self.assign("diag_attention"),
                node,
                self.assign("diag_norm2")
            ]

        return node

    def visit_Call(self, node):
        self.generic_visit(node)

        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "output"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "graph"
        ):
            names = [
                x.id if isinstance(x, ast.Name) else None
                for x in node.args
            ]

            expected = [
                "result", "seq", "context", "search0",
                "search1", "task", "jet", "ihq", "sibling"
            ]

            if names == expected:
                self.found["output"] += 1
                node.args.extend([
                    ast.Name(id=n, ctx=ast.Load())
                    for n in (
                        "diag_norm1",
                        "diag_attention",
                        "diag_norm2"
                    )
                ])

        return node

capture = CaptureStages()
tree = capture.visit(ast.parse(graph_file.read_text()))
ast.fix_missing_locations(tree)

print("GRAPH CAPTURE LOCATIONS:", capture.found, flush=True)

if capture.found != {
    "moe_norm1": 1,
    "moe_norm2": 1,
    "output": 1
}:
    raise SystemExit("STOP: Graph structure needs adjustment")

module_name = "cta_max.grecbase_fusion_order_correct_max_branch_diag"
module = types.ModuleType(module_name)
module.__file__ = str(graph_file)
module.__package__ = "cta_max"

sys.modules[module_name] = module
exec(compile(tree, str(graph_file), "exec"), module.__dict__)

runner_source = runner_file.read_text()

runner_source, count = re.subn(
    r"if\s+len\(outputs\)\s*!=\s*9\s*:",
    "if len(outputs) < 9:",
    runner_source
)

if count != 1:
    raise SystemExit("STOP: Runner output count check changed")

scope = {
    "__name__": "__main__",
    "__file__": str(runner_file),
    "__package__": None
}

print("Running MAX with three captured stages...", flush=True)

with contextlib.redirect_stdout(io.StringIO()):
    exec(
        compile(runner_source, str(runner_file), "exec"),
        scope
    )

outputs = scope["outputs"]

if len(outputs) != 12:
    raise SystemExit(f"Expected 12 outputs, got {len(outputs)}")

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
    np.asarray(
        output.to_numpy(), dtype=np.float32
    ).reshape(1, 256)
    for output in outputs[1:9]
]

x = torch.from_numpy(np.stack(branches, axis=1))

with torch.no_grad():
    pt_norm1 = n1(x)
    pt_attention = att(pt_norm1)
    pt_norm2 = n2(pt_attention)

print("\n=== FINAL PYTORCH VS MAX STAGES ===")

first_failure = None

for name, max_output, pt_output in [
    ("MOE_NORM1", outputs[9], pt_norm1),
    ("ATTENTION_POOLING", outputs[10], pt_attention),
    ("MOE_NORM2", outputs[11], pt_norm2)
]:
    a = np.asarray(max_output.to_numpy(), dtype=np.float32)
    b = pt_output.detach().numpy().astype(np.float32)

    if a.shape != b.shape:
        print(name, "SHAPE MISMATCH:", a.shape, b.shape)
        first_failure = first_failure or name
        continue

    d = np.abs(a.astype(np.float64) - b.astype(np.float64))
    match = bool(np.allclose(a, b, rtol=1e-3, atol=1e-3))

    print(
        name,
        "PASS" if match else "FAIL",
        "MAX_DIFF:", float(d.max()),
        "MEAN_DIFF:", float(d.mean())
    )

    if not match and first_failure is None:
        first_failure = name

print("\nFIRST DIFFERENT STAGE:", first_failure or "NONE")
print("ORIGINAL FILES: UNCHANGED")
PY
