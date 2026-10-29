python3 -S -B - <<'PY'
from pathlib import Path
import ast

dev = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")
repo = Path.cwd()

src = repo / "artifacts/v1.168-max/cta_max/parallel_transformer_block_2layers.py"
graph = dev / "grecbase_fusion_full_head_72_max_batch2_shapes.py"
runner = dev / "run_live_max_inference_batch2_shapes.py"

fixed_block = dev / "parallel_transformer_block_2layers_batch2_fix.py"
fixed_graph = dev / "grecbase_fusion_full_head_72_max_batch2_blockfix.py"
fixed_runner = dev / "run_live_max_inference_batch2_blockfix.py"

assert repo.name == "rt-pzaas-cta-offers-v1", "STOP: Wrong repository"
assert all(p.is_file() for p in (src, graph, runner)), "STOP: Source missing"
assert all(not p.exists() for p in (fixed_block, fixed_graph, fixed_runner)), \
    "STOP: Candidate already exists"

tree = ast.parse(src.read_text())

assert not any(
    isinstance(n, ast.ImportFrom) and n.level
    for n in ast.walk(tree)
), "STOP: Relative imports require separate handling"

class FixBatchValidLength(ast.NodeTransformer):
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
            and isinstance(node.args[0], ast.Name)
            and node.args[0].id == "valid_length"
        ):
            return node

        try:
            shape = ast.literal_eval(node.args[1])
        except (ValueError, TypeError):
            return node

        if shape == [1, 1, 1, 1]:
            node.args[1] = ast.List(
                elts=[ast.Constant(x) for x in (2, 1, 1, 1)],
                ctx=ast.Load()
            )
            self.changes.append(node.lineno)

        return node

fix = FixBatchValidLength()
fix.visit(tree)

assert len(fix.changes) == 1, (
    f"STOP: Expected one valid_length reshape; found {fix.changes}"
)

ast.fix_missing_locations(tree)
block_code = ast.unparse(tree) + "\n"

graph_code = graph.read_text()

old_import = "from cta_max.parallel_transformer_block_2layers import"
new_import = "from parallel_transformer_block_2layers_batch2_fix import"

assert graph_code.count(old_import) == 1, \
    "STOP: Transformer import differs"

graph_code = graph_code.replace(old_import, new_import, 1)

runner_code = runner.read_text()

assert runner_code.count(graph.stem) == 1, \
    "STOP: Runner graph reference differs"

runner_code = runner_code.replace(
    graph.stem, fixed_graph.stem, 1
)

for path, code in (
    (fixed_block, block_code),
    (fixed_graph, graph_code),
    (fixed_runner, runner_code),
):
    compile(code, str(path), "exec")

for path, code in (
    (fixed_block, block_code),
    (fixed_graph, graph_code),
    (fixed_runner, runner_code),
):
    path.write_text(code)
    print("CREATED:", path.name)

print("\nTRANSFORMER VALID_LENGTH FIX: INSTALLED")
print("SHAPE: [1,1,1,1] -> [2,1,1,1]")
print("FIXED LINES:", fix.changes)
print("PYTHON SYNTAX: PASS")
print("GRAPH CONSTRUCTION: NOT YET RETESTED")
print("ORIGINAL TRANSFORMER: UNCHANGED")
print("ORIGINAL DS CODE: UNCHANGED")
print("WORKING NATIVE RELEASE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
