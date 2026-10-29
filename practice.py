python3 -S -B - <<'PY'
from pathlib import Path
import ast
import copy

dev = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")
src = dev / "grecbase_fusion_full_head_72_max.py"
dst = dev / "grecbase_fusion_full_head_72_max_batch2_candidate.py"

assert src.is_file(), f"STOP: Missing {src}"
assert not dst.exists(), "STOP: Batch-2 candidate already exists"

tree = ast.parse(src.read_text())

name = "build_grecbase_fusion_graph_order_correct"
functions = [
    n for n in tree.body
    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    and n.name == name
]
assert len(functions) == 1, "STOP: Graph builder not uniquely found"

fn = functions[0]

graph_calls = [
    n for n in ast.walk(fn)
    if isinstance(n, ast.Call)
    and any(k.arg == "input_types" for k in n.keywords)
]
assert len(graph_calls) == 1, "STOP: Graph input declaration ambiguous"

graph_call = graph_calls[0]
input_kw = next(
    k for k in graph_call.keywords if k.arg == "input_types"
)

class BatchTwoInputs(ast.NodeTransformer):
    def __init__(self):
        self.changed = 0

    def visit_Call(self, node):
        self.generic_visit(node)

        func = node.func
        is_tensor_type = (
            isinstance(func, ast.Name) and func.id == "TensorType"
        ) or (
            isinstance(func, ast.Attribute) and func.attr == "TensorType"
        )

        if is_tensor_type and len(node.args) >= 2:
            shape = node.args[1]

            if isinstance(shape, (ast.List, ast.Tuple)) and shape.elts:
                first = shape.elts[0]

                if isinstance(first, ast.Constant) and first.value == 1:
                    shape.elts[0] = ast.Constant(value=2)
                    self.changed += 1

        return node

transform = BatchTwoInputs()
input_kw.value = transform.visit(input_kw.value)

assert transform.changed > 0, (
    "STOP: No explicit singleton graph input dimensions found"
)

fn.name = name + "_batch2"

ast.fix_missing_locations(tree)
candidate = ast.unparse(tree) + "\n"
compile(candidate, str(dst), "exec")

dst.write_text(candidate)
assert ast.parse(dst.read_text())

print("BATCH-2 GRAPH CANDIDATE: CREATED")
print("GRAPH INPUT SHAPE DECLARATIONS UPDATED:", transform.changed)
print("NEW FUNCTION:", fn.name)
print("PYTHON SYNTAX: PASS")
print("OTHER GRAPH OPERATIONS: REQUIRE BATCH-2 ADAPTATION")
print("BATCH-2 INFERENCE: NOT YET TESTED")
print("WORKING NATIVE RELEASE: UNCHANGED")
print("ORIGINAL DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
print("FILE:", dst)
PY
