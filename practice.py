python3 -S -B - <<'PY'
from pathlib import Path
import ast

dev = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")
graph = dev / "grecbase_fusion_full_head_72_max_batch2_shapes.py"
runner = dev / "run_live_max_inference_batch2_shapes.py"

for p in (graph, runner):
    assert p.is_file(), f"STOP: Missing {p}"

source = graph.read_text()
tree = ast.parse(source)
runner_source = runner.read_text()
runner_tree = ast.parse(runner_source)

fn_name = "build_grecbase_fusion_graph_order_correct_batch2_shapes"
matches = [
    n for n in tree.body
    if isinstance(n, ast.FunctionDef) and n.name == fn_name
]
assert len(matches) == 1, "STOP: Batch-2 graph function missing"

fn = matches[0]
issues = []

for node in ast.walk(fn):
    if isinstance(node, ast.Call):
        name = ast.unparse(node.func)
        if any(x in name for x in (
            "reshape", "broadcast_to", "TensorType",
            "repeat", "tile"
        )):
            args = [ast.unparse(a) for a in node.args]
            for arg in args:
                if arg.startswith(("[1,", "(1,", "[1]", "(1,)")):
                    issues.append((node.lineno, name, arg[:120]))

    elif isinstance(node, ast.Assert):
        expression = ast.unparse(node.test)
        if "shape" in expression or "batch" in expression:
            issues.append((node.lineno, "ASSERT", expression[:120]))

runner_functions = {
    n.name for n in ast.walk(runner_tree)
    if isinstance(n, ast.FunctionDef)
}
assert "infer_max_live_batch2" in runner_functions, \
    "STOP: Batch-2 runner entry missing"

print("=== BATCH-2 GRAPH SAFETY CHECK ===")
print("GRAPH FUNCTION:", fn_name)
print("BATCH RUNNER: FOUND")
print("REMAINING SHAPE ASSUMPTIONS:", len(issues))

for line, kind, detail in sorted(issues):
    print(f"LINE {line} | {kind} | {detail}")

print("\n=== DECISION ===")
if issues:
    print("REVIEW REQUIRED: Remaining fixed-shape assumptions")
else:
    print("STATIC SHAPE CHECK: PASS")
    print("RUNTIME GRAPH COMPILATION: STILL REQUIRED")

print("FILES MODIFIED: NONE")
print("WORKING NATIVE RELEASE: UNCHANGED")
print("ORIGINAL DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
