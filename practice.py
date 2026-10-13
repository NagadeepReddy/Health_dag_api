python - <<'PY'
from pathlib import Path
import ast
import re
import textwrap

base = Path("artifacts/v1.168-max/cta_max")
srcg = base / "grecbase_fusion_seq_isolation_trial.py"
srcr = base / "run_real_sanity_seq_isolation_trial.py"
outg = base / "grecbase_fusion_fusion_stage_trial.py"
outr = base / "run_real_sanity_fusion_stage_trial.py"

for p in (srcg, srcr, base / "real_sanity_pytorch_same_input_verified.npz"):
    if not p.is_file():
        raise SystemExit(f"STOP: Missing verified file: {p}")

g = srcg.read_text()

patterns = [
    (r'''(?m)^([ \t]*)outs\s*=\s*norm\(outs,\s*['"]moe_norm1['"]\)[ \t]*$''',
     "stage_stacked = outs", "before"),
    (r'''(?m)^([ \t]*)outs\s*=\s*norm\(outs,\s*['"]moe_norm1['"]\)[ \t]*$''',
     "stage_norm1 = outs", "after"),
    (r"(?m)^([ \t]*)outs\s*=\s*block\(outs,\s*pos\)[ \t]*$",
     "stage_attention = outs", "after"),
    (r'''(?m)^([ \t]*)outs\s*=\s*norm\(outs,\s*['"]moe_norm2['"]\)[ \t]*$''',
     "stage_norm2 = outs", "after"),
]

for pattern, new_line, position in patterns:
    matches = list(re.finditer(pattern, g))
    if len(matches) != 1:
        raise SystemExit(f"STOP: Fusion stage not unique: {new_line}")
    m = matches[0]
    added = m.group(1) + new_line + "\n"
    if position == "before":
        g = g[:m.start()] + added + g[m.start():]
    else:
        g = g[:m.end()] + "\n" + m.group(1) + new_line + g[m.end():]

tree = ast.parse(g)
calls = [
    n for n in ast.walk(tree)
    if isinstance(n, ast.Call)
    and isinstance(n.func, ast.Attribute)
    and n.func.attr == "output"
    and isinstance(n.func.value, ast.Name)
    and n.func.value.id == "graph"
]
if len(calls) != 1:
    raise SystemExit("STOP: graph.output not unique")

node = calls[0]
lines = g.splitlines(keepends=True)
a = sum(map(len, lines[:node.lineno-1])) + node.col_offset
b = sum(map(len, lines[:node.end_lineno-1])) + node.end_col_offset
call = g[a:b]
i = call.rfind(")")
if i == -1:
    raise SystemExit("STOP: Invalid graph output")

call = (
    call[:i] +
    ", stage_stacked, stage_norm1, stage_attention, stage_norm2" +
    call[i:]
)
g = g[:a] + call + g[b:]
ast.parse(g)

r = srcr.read_text()
old = "cta_max.grecbase_fusion_seq_isolation_trial"
if r.count(old) != 1:
    raise SystemExit("STOP: Existing graph import not unique")

r = r.replace(
    old, "cta_max.grecbase_fusion_fusion_stage_trial", 1
)

if r.count("len(outputs) != 9") != 1:
    raise SystemExit("STOP: Existing diagnostic output contract differs")
r = r.replace("len(outputs) != 9", "len(outputs) != 13", 1)

pattern = re.compile(
    r"(?m)^([ \t]*)outputs\s*=\s*model\.execute\(\*runtime_inputs\)[ \t]*$"
)
matches = list(pattern.finditer(r))
if len(matches) != 1:
    raise SystemExit("STOP: Existing model execution not unique")

code = '''
import sys
import json
import inspect
import torch
import numpy as np
from pathlib import Path

root = Path("artifacts/v1.168")
params = json.loads(
    (root / "config/torch_model_params_base.json").read_text()
)
if isinstance(params, list):
    assert len(params) == 1
    params = params[0]

params["nlp_encoder_path"] = str(root / "config/config.json")
params["transfer_ind"] = True
params["extract_deep_idx"] = -1

sys.path.insert(0, str(root / "utils/dependency-utils"))
from models import GRecBase

pt = GRecBase(**params)
weights = torch.load(
    root / "core-artifact/model_0_base.pt",
    map_location="cpu", weights_only=True
)
if isinstance(weights, dict) and "state_dict" in weights:
    weights = weights["state_dict"]

pt.load_state_dict(weights, strict=True)
pt.eval()

real = torch.load(
    BASE / "real_sanity_model_in.pt",
    map_location="cpu", weights_only=True
)

kwargs = {}
for name, param in inspect.signature(pt.forward).parameters.items():
    key = "task_in" if name == "tasks_in" else name
    if key in real:
        kwargs[name] = real[key]
    elif param.default is inspect.Parameter.empty:
        raise RuntimeError("Missing original input: " + name)

stages = {}

def capture_input(module, args):
    stages["stacked"] = args[0].detach().cpu().numpy()

def capture(name):
    def hook(module, args, result):
        stages[name] = result.detach().cpu().numpy()
    return hook

for name in ("moe_norm1", "att_pooling", "moe_norm2"):
    if not hasattr(pt, name):
        raise RuntimeError("Original fusion module missing: " + name)

hooks = [
    pt.moe_norm1.register_forward_pre_hook(capture_input),
    pt.moe_norm1.register_forward_hook(capture("norm1")),
    pt.att_pooling.register_forward_hook(capture("attention")),
    pt.moe_norm2.register_forward_hook(capture("norm2")),
]

try:
    with torch.inference_mode():
        pt_final = pt(**kwargs).detach().cpu().numpy()
finally:
    for hook in hooks:
        hook.remove()

with np.load(
    BASE / "real_sanity_pytorch_same_input_verified.npz",
    allow_pickle=False
) as saved:
    same = np.allclose(
        pt_final, saved["final"], rtol=1e-6, atol=1e-6
    )

print("\\n=== FUSION STAGE NUMERICAL PARITY ===", flush=True)
print("ORIGINAL REFERENCE REPRODUCED:", bool(same), flush=True)
if not same:
    raise RuntimeError("Original PyTorch reference differs")

for index, stage in enumerate(
    ("stacked", "norm1", "attention", "norm2"), start=9
):
    mx = np.asarray(outputs[index].to_numpy(), dtype=np.float32)
    original = np.asarray(stages[stage], dtype=np.float32)

    print(
        stage.upper(),
        "PYTORCH:", original.shape,
        "MAX:", mx.shape,
        flush=True
    )

    if mx.shape != original.shape:
        print("SHAPE MISMATCH", flush=True)
        continue

    diff = np.abs(
        mx.astype(np.float64) - original.astype(np.float64)
    )
    print(
        "MATCH:",
        bool(np.allclose(mx, original, rtol=1e-3, atol=1e-3)),
        "MAX_DIFF:", float(diff.max()),
        "MEAN_DIFF:", float(diff.mean()),
        flush=True
    )

print("WORKING SOURCE AND WEIGHTS UNCHANGED", flush=True)
'''

m = matches[0]
insert = "\n" + textwrap.indent(
    textwrap.dedent(code).strip("\n"),
    m.group(1)
)
r = r[:m.end()] + insert + r[m.end():]
ast.parse(r)

for p, content in ((outg, g), (outr, r)):
    if p.exists() and p.read_text() != content:
        raise SystemExit(f"STOP: Existing trial differs: {p}")

for p, content in ((outg, g), (outr, r)):
    if not p.exists():
        p.write_text(content)
    print("READY:", p.name)

print("PRODUCTION MAX / PYTORCH / DS FILES UNCHANGED")
PY

podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  artifacts/v1.168-max/cta_max/run_real_sanity_fusion_stage_trial.py
