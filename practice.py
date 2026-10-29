set -eu

REPO=/application1/sajjna8/rt-pzaas-cta-offers-v1
DEV=/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029

python3 -S -B - <<'PY'
from pathlib import Path
import ast
import hashlib

repo = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1")
dev = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")

src = repo / "artifacts/v1.168-max/cta_max/sibling_context_max.py"
graph_src = dev / "grecbase_fusion_full_head_72_max_batch2_blockfix.py"

fixed = dev / "sibling_context_max_batch2_fix.py"
graph_dst = dev / "grecbase_fusion_full_head_72_max_batch2_siblingfix.py"

for p in (src, graph_src):
    assert p.is_file(), f"STOP: Missing source {p}"

original_hash = hashlib.sha256(src.read_bytes()).hexdigest()
tree = ast.parse(src.read_text())
changes = []

class FixSiblingBatch(ast.NodeTransformer):
    def visit_Call(self, node):
        self.generic_visit(node)

        if not (
            isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "ops"
            and node.func.attr == "reshape"
            and len(node.args) >= 2
        ):
            return node

        try:
            shape = ast.literal_eval(node.args[1])
        except (ValueError, TypeError):
            return node

        if tuple(shape) == (1, 128):
            changes.append(node.lineno)
            node.args[1] = ast.List(
                elts=[ast.Constant(2), ast.Constant(128)],
                ctx=ast.Load()
            )

        return node

FixSiblingBatch().visit(tree)

assert len(changes) == 1, (
    f"STOP: Expected one sibling reshape, found {changes}"
)

ast.fix_missing_locations(tree)
fixed_code = ast.unparse(tree) + "\n"

graph_tree = ast.parse(graph_src.read_text())
imports = [
    n for n in ast.walk(graph_tree)
    if isinstance(n, ast.ImportFrom)
    and n.module == "cta_max.sibling_context_max"
    and any(a.name == "sibling_context_forward" for a in n.names)
]

assert len(imports) == 1, (
    "STOP: Expected sibling-context import not uniquely found"
)

imports[0].module = "sibling_context_max_batch2_fix"

ast.fix_missing_locations(graph_tree)
graph_code = ast.unparse(graph_tree) + "\n"

for path, code in ((fixed, fixed_code), (graph_dst, graph_code)):
    compile(code, str(path), "exec")

    if path.exists():
        assert path.read_text() == code, (
            f"STOP: Existing candidate differs: {path}"
        )
        print("ALREADY VERIFIED:", path.name)
    else:
        path.write_text(code)
        print("CREATED:", path.name)

assert hashlib.sha256(src.read_bytes()).hexdigest() == original_hash

print("SIBLING BATCH-2 RESHAPE: [1,128] -> [2,128]")
print("FIXED ORIGINAL LINE:", changes[0])
print("PYTHON SYNTAX: PASS")
print("ORIGINAL SIBLING CODE: UNCHANGED")
print("WORKING RELEASE: UNCHANGED")
PY

echo "=== REAL BATCH-2 GRAPH CONSTRUCTION ==="

timeout 120s podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --network none \
  --memory 2g --cpus 2 --pids-limit 64 \
  --tmpfs /tmp:rw,size=256m \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e XDG_CACHE_HOME=/tmp \
  -e PYTHONPATH=/batch2:/workspace/artifacts/v1.168-max \
  -v "$REPO:/workspace:ro" \
  -v "$DEV:/batch2:ro" \
  -w /workspace \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -B - <<'PY'
import traceback
import sys

try:
    from max.driver import CPU
    from max.graph import DeviceRef
    from grecbase_fusion_full_head_72_max_batch2_siblingfix import (
        build_grecbase_fusion_graph_order_correct_batch2_shapes
    )

    graph = build_grecbase_fusion_graph_order_correct_batch2_shapes(
        DeviceRef.from_device(CPU())
    )

    print("BATCH-2 GRAPH CONSTRUCTION: PASS")
    print("GRAPH INPUT COUNT:", len(graph.inputs))

    for i, item in enumerate(graph.inputs):
        print("INPUT", i, "SHAPE:", item.type.shape)

except Exception:
    print("BATCH-2 GRAPH CONSTRUCTION: FAIL")
    traceback.print_exc()
    sys.exit(1)

print("REAL BATCH-2 INFERENCE: NOT YET PERFORMED")
print("WORKING NATIVE RELEASE: UNCHANGED")
print("ORIGINAL DS CODE: UNCHANGED")
PY
