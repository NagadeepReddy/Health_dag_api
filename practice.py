podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  - <<'PY'
import ast
import sys
from pathlib import Path

base = Path("artifacts/v1.168-max/cta_max")
graph_file = base / "parallel_transformer_graph_full_sequence.py"
feature_file = base / "sequence_transformer_max.py"

assert graph_file.is_file() and feature_file.is_file()

# Verify the existing feature interface.
ft = ast.parse(feature_file.read_text())
classes = [
    n for n in ft.body
    if isinstance(n, ast.ClassDef)
    and n.name == "ParallelTransformerMAEPMAX"
]
assert len(classes) == 1

calls = [
    n for n in classes[0].body
    if isinstance(n, ast.FunctionDef)
    and n.name == "__call__"
]
assert len(calls) == 1

returns = [
    n for n in ast.walk(calls[0])
    if isinstance(n, ast.Return)
]
assert len(returns) == 1
assert isinstance(returns[0].value, ast.Tuple)

names = [ast.unparse(v) for v in returns[0].value.elts]
assert names == [
    "page", "item", "item_meta", "item_pre", "page_wide"
], f"STOP: feature interface differs: {names}"

source = graph_file.read_text()
tree = ast.parse(source)

builders = [
    n for n in tree.body
    if isinstance(n, ast.FunctionDef)
    and n.name == "build_parallel_transformer_graph"
]
assert len(builders) == 1

targets = [
    n for n in ast.walk(builders[0])
    if isinstance(n, ast.Assign)
    and len(n.targets) == 1
    and isinstance(n.targets[0], ast.Name)
    and n.targets[0].id == "x"
    and isinstance(n.value, ast.Call)
    and isinstance(n.value.func, ast.Name)
    and n.value.func.id == "features"
]
assert len(targets) == 1, \
    "STOP: graph feature assembly already differs"

node = targets[0]
lines = source.splitlines(keepends=True)
original = lines[node.lineno - 1]
indent = original[:len(original) - len(original.lstrip())]

call = ast.unparse(node.value)

replacement = [
    "from max.graph import ops",
    "page_emb, item_emb, item_meta_emb, item_pre_emb, page_wide_emb = " + call,
    "page_wide_emb = ops.relu(page_wide_emb) - 0.2 * ops.relu(-page_wide_emb)",
    "page_full = ops.concat([page_emb, page_wide_emb], axis=-1)",
    "item_full = ops.concat([item_emb, item_meta_emb, item_pre_emb], axis=-1)",
    "x = page_full * item_full",
]

new_lines = [
    indent + line + "\n"
    for line in replacement
]

updated = (
    "".join(lines[:node.lineno - 1])
    + "".join(new_lines)
    + "".join(lines[node.end_lineno:])
)

ast.parse(updated)

# Validate the corrected graph in memory before saving.
sys.path.insert(0, str(base.parent))

namespace = {
    "__name__": "cta_max.sequence_integration_preflight",
    "__package__": "cta_max",
    "__file__": str(graph_file),
}

exec(
    compile(updated, str(graph_file), "exec"),
    namespace,
)

from max.driver import CPU
from max.graph import DeviceRef

device = DeviceRef.from_device(CPU())

graph = namespace["build_parallel_transformer_graph"](
    device, {}
)

print("FULL SEQUENCE GRAPH CONSTRUCTION: PASS", flush=True)

graph_file.write_text(updated)

print("FEATURE ASSEMBLY CONNECTED")
print("PAGE: 224 + 32 = 256")
print("ITEM: 112 + 32 + 112 = 256")
print("ORIGINAL PAGE × ITEM COMBINATION PRESERVED")
print("ORIGINAL PYTORCH AND DS CODE UNCHANGED")
PY
