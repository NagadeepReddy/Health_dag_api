python - <<'PY'
from pathlib import Path
import ast
import re

base = Path("artifacts/v1.168-max/cta_max")
source_graph = base / "grecbase_fusion_fusion_stage_trial.py"
source_runner = base / "run_real_sanity_fusion_stage_trial.py"

trial_graph = base / "grecbase_fusion_verified_wiring_trial.py"
trial_runner = base / "run_real_sanity_verified_wiring_trial.py"

for p in (source_graph, source_runner):
    if not p.is_file():
        raise SystemExit(f"STOP: Existing working diagnostic missing: {p}")

code = source_graph.read_text()
tree = ast.parse(code)

# Use the eight tensors already exposed by the successful
# eight-branch comparison, in the original verified order.
output_calls = [
    n for n in ast.walk(tree)
    if isinstance(n, ast.Call)
    and isinstance(n.func, ast.Attribute)
    and isinstance(n.func.value, ast.Name)
    and n.func.value.id == "graph"
    and n.func.attr == "output"
]

if len(output_calls) != 1:
    raise SystemExit("STOP: Graph output not unique")

args = output_calls[0].args
if len(args) == 1 and isinstance(args[0], (ast.List, ast.Tuple)):
    args = args[0].elts

if len(args) != 13:
    raise SystemExit(
        f"STOP: Expected 13 verified graph outputs, found {len(args)}"
    )

branches = [
    ast.get_source_segment(code, n)
    for n in args[1:9]
]

if len(branches) != 8 or any(x is None for x in branches):
    raise SystemExit("STOP: Cannot safely resolve all eight branches")

# This anchor is immediately before the original first fusion norm.
anchors = [
    n for n in ast.walk(tree)
    if isinstance(n, ast.Assign)
    and len(n.targets) == 1
    and isinstance(n.targets[0], ast.Name)
    and n.targets[0].id == "stage_stacked"
    and isinstance(n.value, ast.Name)
    and n.value.id == "outs"
]

if len(anchors) != 1:
    raise SystemExit("STOP: Fusion stack anchor not unique")

node = anchors[0]
lines = code.splitlines(keepends=True)
line = lines[node.lineno - 1]
indent = re.match(r"[ \t]*", line).group()

insertion = (
    indent + "# TRIAL: wire the eight verified branch outputs into fusion\n"
    + indent + "outs = ops.stack([\n"
    + "".join(indent + "    " + x + ",\n" for x in branches)
    + indent + "], axis=1)\n"
)

lines.insert(node.lineno - 1, insertion)
updated_graph = "".join(lines)
ast.parse(updated_graph)

runner = source_runner.read_text()

old_import = "cta_max.grecbase_fusion_fusion_stage_trial"
new_import = "cta_max.grecbase_fusion_verified_wiring_trial"

if runner.count(old_import) != 1:
    raise SystemExit("STOP: Existing runner import not unique")

updated_runner = runner.replace(old_import, new_import, 1)
ast.parse(updated_runner)

for p, content in (
    (trial_graph, updated_graph),
    (trial_runner, updated_runner),
):
    if p.exists() and p.read_text() != content:
        raise SystemExit(f"STOP: Existing trial differs: {p}")

for p, content in (
    (trial_graph, updated_graph),
    (trial_runner, updated_runner),
):
    if not p.exists():
        p.write_text(content)
    print("READY:", p.name)

print("VERIFIED BRANCH TENSORS:")
for i, name in enumerate(branches):
    print(i, name)

print("ORIGINAL MAX, PYTORCH, DS AND WEIGHTS UNCHANGED")
PY

podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  artifacts/v1.168-max/cta_max/run_real_sanity_verified_wiring_trial.py
