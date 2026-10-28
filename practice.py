cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

python3 -S -B - <<'PY'
from pathlib import Path
import ast
import shutil

base = Path("/application1/cta_max_true_batch_dev_20261028")
src = base / "cta_max"
draft = src / "grecbase_fusion_batch2_draft.py"
dst = base / "batch2_candidate"
target = dst / "cta_max"

assert src.is_dir() and draft.is_file(), "STOP: Batch sources missing"
assert not dst.exists(), "STOP: Candidate already exists"
assert shutil.disk_usage("/application1").free > 2 * 1024**3, \
    "STOP: Insufficient disk space"

# Identify only dependencies used by the active graph.
entry = src / "grecbase_fusion_full_head_72_max.py"
pending = [entry]
visited = set()

while pending:
    p = pending.pop()
    if p in visited:
        continue
    visited.add(p)

    tree = ast.parse(p.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.module.startswith("cta_max."):
                dep = src / (
                    node.module[8:].replace(".", "/") + ".py"
                )
                if dep.is_file() and dep not in visited:
                    pending.append(dep)

assert len(visited) >= 2, "STOP: Dependency map incomplete"

# Keep a complete isolated package for normal Python imports.
shutil.copytree(src, target)

# Use the already prepared batch-2 graph declarations.
(target / entry.name).write_bytes(draft.read_bytes())

changes = {}

for original in sorted(visited):
    if original == entry:
        continue

    p = target / original.relative_to(src)
    source = p.read_text()
    tree = ast.parse(source)

    offsets = [0]
    for line in source.splitlines(keepends=True):
        offsets.append(offsets[-1] + len(line))

    replacements = set()

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        name = ast.unparse(node.func)

        # Only explicit tensor reshapes with a literal
        # leading batch dimension. Other dimensions stay intact.
        if name not in ("ops.reshape", "np.reshape", "numpy.reshape"):
            continue
        if len(node.args) < 2:
            continue

        shape = node.args[1]
        if not isinstance(shape, (ast.List, ast.Tuple)):
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
        replacements.add((start, end))

    updated = source
    for start, end in sorted(replacements, reverse=True):
        updated = updated[:start] + "2" + updated[end:]

    ast.parse(updated)
    if replacements:
        p.write_text(updated)
        changes[p.name] = len(replacements)

for p in target.rglob("*.py"):
    ast.parse(p.read_text())

print("BATCH-2 INTERNAL CANDIDATE: CREATED")
print("ACTIVE MODULES REVIEWED:", len(visited))
print("INTERNAL MODULES UPDATED:", len(changes))
print("RESHAPE DECLARATIONS UPDATED:", sum(changes.values()))

for name, count in sorted(changes.items()):
    print(f"  {name}: {count}")

print("PYTHON SYNTAX: PASS")
print("CANDIDATE:", target)
print("OTHER BATCH-SENSITIVE OPERATIONS: STILL NEED VALIDATION")
print("TRUE BATCH INFERENCE: NOT YET PROVEN")
print("WORKING HTTP 200: UNCHANGED")
print("DS CODE: UNCHANGED")
print("MODEL STARTUP: NOT PERFORMED")
PY
