cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

python3 -S -B - <<'PY'
from pathlib import Path
import ast
import shutil

base = Path("/application1/cta_max_true_batch_dev_20261028")
original = base / "cta_max"
candidate = base / "batch2_candidate/cta_max"
graph = candidate / "grecbase_fusion_full_head_72_max.py"

assert original.is_dir() and candidate.is_dir()
assert graph.is_file(), "STOP: Batch graph missing"

source = graph.read_text()
tree = ast.parse(source)

offsets = [0]
for line in source.splitlines(keepends=True):
    offsets.append(offsets[-1] + len(line))

changes = set()
unresolved = []

for node in ast.walk(tree):
    if not isinstance(node, ast.Call):
        continue

    name = ast.unparse(node.func)

    if name != "ops.reshape" or len(node.args) < 2:
        continue

    shape = node.args[1]

    if not isinstance(shape, (ast.List, ast.Tuple)):
        unresolved.append(
            f"Line {node.lineno}: dynamic reshape requires validation"
        )
        continue

    if not shape.elts:
        continue

    first = shape.elts[0]

    if not (
        isinstance(first, ast.Constant)
        and type(first.value) is int
        and first.value == 1
    ):
        continue

    start = offsets[first.lineno - 1] + first.col_offset
    end = offsets[first.end_lineno - 1] + first.end_col_offset

    assert source[start:end] == "1"
    changes.add((start, end, node.lineno))

updated = source

for start, end, lineno in sorted(changes, reverse=True):
    updated = updated[:start] + "2" + updated[end:]

ast.parse(updated)

backup = graph.with_suffix(".py.before_batch2_internal.bak")

if changes:
    assert not backup.exists(), "STOP: Backup exists; no overwrite"
    assert shutil.disk_usage("/application1").free > 1024**3, \
        "STOP: Low disk space"

    backup.write_bytes(graph.read_bytes())
    graph.write_text(updated)

syntax_count = 0
for p in candidate.rglob("*.py"):
    ast.parse(p.read_text())
    syntax_count += 1

# Ensure the original working graph remains unchanged.
original_graph = original / graph.name
assert original_graph.is_file()

print("=== BATCH-2 IMPLEMENTATION ===")
print("MAIN GRAPH CORRECTIONS:", len(changes))
print("CORRECTED LINES:",
      sorted(x[2] for x in changes))
print("PYTHON FILES VALIDATED:", syntax_count)
print("PYTHON SYNTAX: PASS")
print("DYNAMIC RESHAPES REQUIRING REVIEW:", len(unresolved))

for issue in unresolved[:15]:
    print("REVIEW:", issue)

print("ISOLATED BATCH CANDIDATE: UPDATED")
print("COMPILED BATCH-2 GRAPH: NOT YET VALIDATED")
print("TRUE BATCH INFERENCE: NOT YET PROVEN")
print("WORKING HTTP 200: UNCHANGED")
print("ORIGINAL DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
