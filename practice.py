cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path
import ast

base = Path("/application1/cta_max_true_batch_dev_20261028/cta_max")
src = base / "grecbase_fusion_full_head_72_max.py"
dst = base / "grecbase_fusion_batch2_draft.py"

assert src.is_file(), "STOP: Original batch graph missing"
assert not dst.exists(), "STOP: Batch-2 draft already exists"

source = src.read_text()
tree = ast.parse(source)
graph_calls = [
    n for n in ast.walk(tree)
    if isinstance(n, ast.Call)
    and isinstance(n.func, ast.Name)
    and n.func.id == "Graph"
]

assert len(graph_calls) == 1, "STOP: Graph definition differs"

graph = graph_calls[0]
tensor_calls = [
    n for n in ast.walk(graph)
    if isinstance(n, ast.Call)
    and isinstance(n.func, ast.Name)
    and n.func.id == "TensorType"
]

lines = source.splitlines(keepends=True)
offsets = [0]
for line in lines:
    offsets.append(offsets[-1] + len(line))

replacements = []

for call in tensor_calls:
    shapes = [
        x for x in call.args
        if isinstance(x, (ast.List, ast.Tuple))
    ]
    shapes += [
        kw.value for kw in call.keywords
        if kw.arg == "shape"
        and isinstance(kw.value, (ast.List, ast.Tuple))
    ]

    for shape in shapes:
        if not shape.elts:
            continue
        first = shape.elts[0]
        if isinstance(first, ast.Constant) and type(first.value) is int and first.value == 1:
            start = offsets[first.lineno - 1] + first.col_offset
            end = offsets[first.end_lineno - 1] + first.end_col_offset
            assert source[start:end] == "1"
            replacements.append((start, end))

assert replacements, "STOP: No static batch dimensions found"

updated = source
for start, end in sorted(set(replacements), reverse=True):
    updated = updated[:start] + "2" + updated[end:]

ast.parse(updated)
dst.write_text(updated)

print("BATCH-2 GRAPH INPUT DRAFT: CREATED")
print("INPUT SHAPE DECLARATIONS UPDATED:", len(set(replacements)))
print("SYNTAX: PASS")
print("LOCATION:", dst)
print("INTERNAL GRAPH BATCHING: STILL PENDING")
print("TRUE BATCH INFERENCE: NOT YET TESTED")
print("WORKING HTTP 200: UNCHANGED")
print("DS CODE: UNCHANGED")
print("MODEL STARTUP: NOT PERFORMED")
PY
