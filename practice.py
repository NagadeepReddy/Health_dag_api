python3 -S -B - <<'PY'
from pathlib import Path
import ast

dev = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")
src = dev / "run_live_max_inference.py"
graph = dev / "grecbase_fusion_full_head_72_max_batch2_candidate.py"
packer = dev / "cta_batch2_input_pack.py"
dst = dev / "run_live_max_inference_batch2.py"

for p in (src, graph, packer):
    assert p.is_file(), f"STOP: Missing {p}"

assert not dst.exists(), "STOP: Batch-2 runner already exists"

original = src.read_text()
tree = ast.parse(original)
graph_tree = ast.parse(graph.read_text())
packer_tree = ast.parse(packer.read_text())

assert any(
    isinstance(n, ast.FunctionDef)
    and n.name == "build_grecbase_fusion_graph_order_correct_batch2"
    for n in graph_tree.body
), "STOP: Batch-2 graph function missing"

for name in ("pack_two_real_inputs", "split_two_max_outputs"):
    assert any(
        isinstance(n, ast.FunctionDef) and n.name == name
        for n in packer_tree.body
    ), f"STOP: Missing {name}"

replacements = {
    "def infer_max_live(model_in):":
        "def _infer_max_live_batch2_raw(model_in_a, model_in_b):",

    "labels, arrays = build_real_inputs(model_in=model_in)":
        "labels, arrays = pack_two_real_inputs(\n"
        "        build_real_inputs(model_in=model_in_a),\n"
        "        build_real_inputs(model_in=model_in_b),\n"
        "    )",

    "graph = build_grecbase_fusion_graph_order_correct(device_ref)":
        "graph = build_grecbase_fusion_graph_order_correct_batch2(device_ref)",
}

for old, new in replacements.items():
    assert original.count(old) == 1, (
        f"STOP: Expected exactly one occurrence: {old}"
    )
    original = original.replace(old, new, 1)

imports = (
    "from grecbase_fusion_full_head_72_max_batch2_candidate "
    "import build_grecbase_fusion_graph_order_correct_batch2\n"
    "from cta_batch2_input_pack import "
    "pack_two_real_inputs, split_two_max_outputs\n\n"
)

anchor = "def _infer_max_live_batch2_raw("
assert original.count(anchor) == 1

original = original.replace(anchor, imports + anchor, 1)

wrapper = '''

def infer_max_live_batch2(model_in_a, model_in_b):
    """Execute one batch-2 MAX graph and return separate sample outputs."""
    output = _infer_max_live_batch2_raw(model_in_a, model_in_b)
    first, second = split_two_max_outputs(output)
    return first, second
'''

candidate = original.rstrip() + "\n" + wrapper
ast.parse(candidate)
compile(candidate, str(dst), "exec")

dst.write_text(candidate)
assert dst.read_text() == candidate

print("REAL CTA BATCH-2 INFERENCE RUNNER: CREATED")
print("REAL MODEL INPUTS: 2")
print("MAX GRAPH EXECUTION: 1 CALL CONFIGURED")
print("EXPECTED OUTPUT: TWO (1,2048) RESULTS")
print("PYTHON SYNTAX: PASS")
print("GRAPH INTERNAL SHAPES: NOT YET VALIDATED")
print("REAL BATCH-2 EXECUTION: NOT YET PERFORMED")
print("WORKING RELEASE: UNCHANGED")
print("ORIGINAL DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
print("FILE:", dst)
PY
