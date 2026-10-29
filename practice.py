python3 -S -B - <<'PY'
from pathlib import Path
import ast

dev = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")

graph_src = dev / "grecbase_fusion_full_head_72_max_batch2_candidate.py"
runner_src = dev / "run_live_max_inference_batch2.py"

graph_dst = dev / "grecbase_fusion_full_head_72_max_batch2_shapes.py"
runner_dst = dev / "run_live_max_inference_batch2_shapes.py"

for p in (graph_src, runner_src):
    assert p.is_file(), f"STOP: Missing {p}"

for p in (graph_dst, runner_dst):
    assert not p.exists(), f"STOP: Already exists: {p}"

tree = ast.parse(graph_src.read_text())

old_fn = "build_grecbase_fusion_graph_order_correct_batch2"
new_fn = old_fn + "_shapes"

matches = [
    n for n in tree.body
    if isinstance(n, ast.FunctionDef) and n.name == old_fn
]
assert len(matches) == 1, "STOP: Batch-2 graph function ambiguous"

fn = matches[0]

class BatchTwoReshapes(ast.NodeTransformer):
    def __init__(self):
        self.changes = []

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

        shape = node.args[1]

        if not isinstance(shape, (ast.List, ast.Tuple)):
            return node

        if not shape.elts:
            return node

        first = shape.elts[0]

        if isinstance(first, ast.Constant) and first.value == 1:
            self.changes.append(
                (node.lineno, ast.unparse(shape))
            )
            shape.elts[0] = ast.Constant(value=2)

        return node

transform = BatchTwoReshapes()
transform.visit(fn)

assert transform.changes, (
    "STOP: No literal batch-leading ops.reshape calls found; "
    "manual graph adaptation required"
)

fn.name = new_fn

ast.fix_missing_locations(tree)
graph_code = ast.unparse(tree) + "\n"
compile(graph_code, str(graph_dst), "exec")

runner = runner_src.read_text()

old_module = graph_src.stem
new_module = graph_dst.stem

assert runner.count(old_module) == 1, (
    "STOP: Runner graph module reference differs"
)
assert runner.count(old_fn) == 2, (
    "STOP: Runner graph function references differ"
)

runner = runner.replace(old_module, new_module, 1)
runner = runner.replace(old_fn, new_fn)

ast.parse(runner)
compile(runner, str(runner_dst), "exec")

graph_dst.write_text(graph_code)
runner_dst.write_text(runner)

print("BATCH-2 INTERNAL SHAPE CANDIDATE: CREATED")
print("RESHAPE OPERATIONS UPDATED:", len(transform.changes))

for line, shape in transform.changes:
    print(f"LINE {line}: {shape} -> leading dimension 2")

print("BATCH-2 RUNNER: CONNECTED")
print("PYTHON SYNTAX: PASS")
print("OTHER INTERNAL GRAPH OPERATIONS: NOT YET VALIDATED")
print("REAL MAX BATCH EXECUTION: NOT YET PERFORMED")
print("WORKING RELEASE: UNCHANGED")
print("ORIGINAL DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
print("GRAPH:", graph_dst)
print("RUNNER:", runner_dst)
PY
