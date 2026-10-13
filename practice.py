python - <<'PY'
from pathlib import Path
import ast
import re

base = Path("artifacts/v1.168-max/cta_max")

graph_src = base / "grecbase_fusion_verified_wiring_trial.py"
runner_src = base / "run_real_sanity_verified_wiring_trial.py"

graph_dst = base / "grecbase_fusion_pytorch_order_trial.py"
runner_dst = base / "run_real_sanity_pytorch_order_trial.py"

for p in (graph_src, runner_src):
    if not p.is_file():
        raise SystemExit(f"STOP: Missing existing working file: {p}")

source = graph_src.read_text()
tree = ast.parse(source)

old_order = [
    "seq", "context", "search0", "search1",
    "task", "jet", "ihq", "sibling"
]
correct_order = [
    "seq", "context", "search0", "search1",
    "jet", "ihq", "sibling", "task"
]

candidates = []

for node in ast.walk(tree):
    if not isinstance(node, ast.Assign):
        continue
    if not any(
        isinstance(t, ast.Name) and t.id == "outs"
        for t in node.targets
    ):
        continue

    call = node.value
    if not (
        isinstance(call, ast.Call)
        and isinstance(call.func, ast.Attribute)
        and call.func.attr == "stack"
        and len(call.args) == 1
        and isinstance(call.args[0], ast.List)
    ):
        continue

    items = call.args[0].elts
    names = []

    for item in items:
        if not (
            isinstance(item, ast.Call)
            and isinstance(item.func, ast.Attribute)
            and item.func.attr == "reshape"
            and item.args
            and isinstance(item.args[0], ast.Name)
        ):
            break
        names.append(item.args[0].id)

    if names == old_order:
        candidates.append((node, call.args[0], items))

if len(candidates) != 1:
    raise SystemExit(
        f"STOP: Expected one incorrect active stack, "
        f"found {len(candidates)}. Nothing changed."
    )

node, list_node, items = candidates
parts = source.splitlines(keepends=True)

def offset(line, col):
    return sum(len(x) for x in parts[:line - 1]) + col

start = offset(list_node.lineno, list_node.col_offset)
end = offset(list_node.end_lineno, list_node.end_col_offset)

expressions = {
    name: ast.get_source_segment(source, item)
    for name, item in zip(old_order, items)
}

indent = re.match(
    r"[ \t]*", parts[node.lineno - 1]
).group()

replacement = "[\n"
for name in correct_order:
    replacement += indent + "    " + expressions[name] + ",\n"
replacement += indent + "]"

updated_graph = source[:start] + replacement + source[end:]
ast.parse(updated_graph)

runner = runner_src.read_text()

old_import = "cta_max.grecbase_fusion_verified_wiring_trial"
new_import = "cta_max.grecbase_fusion_pytorch_order_trial"

if runner.count(old_import) != 1:
    raise SystemExit("STOP: Runner import not uniquely found")

updated_runner = runner.replace(old_import, new_import, 1)
ast.parse(updated_runner)

for p, content in (
    (graph_dst, updated_graph),
    (runner_dst, updated_runner),
):
    if p.exists() and p.read_text() != content:
        raise SystemExit(f"STOP: Existing trial differs: {p}")

for p, content in (
    (graph_dst, updated_graph),
    (runner_dst, updated_runner),
):
    if not p.exists():
        p.write_text(content)

print("CORRECTED FUSION ORDER:")
print(" → ".join(correct_order))
print("PYTORCH/DS AND EXISTING MAX FILES UNCHANGED")
PY

podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  artifacts/v1.168-max/cta_max/run_real_sanity_pytorch_order_trial.py
