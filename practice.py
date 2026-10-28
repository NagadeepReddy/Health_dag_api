cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path
import ast
import shutil

p = Path(
    "/application1/cta_max_true_batch_dev_20261028/"
    "batch2_candidate/cta_max/grecbase_fusion_full_head_72_max.py"
)
assert p.is_file(), "STOP: Batch candidate missing"
assert shutil.disk_usage("/application1").free > 2 * 1024**3, "STOP: Low disk space"

src = p.read_text()
marker = "CTA_BATCH_SIBLING_POOL_FIX"
assert marker not in src, "STOP: Fix already installed"

tree = ast.parse(src)
matches = [
    n for n in ast.walk(tree)
    if isinstance(n, ast.Assign)
    and any(isinstance(t, ast.Name) and t.id == "sibling" for t in n.targets)
]

assert len(matches) == 1, "STOP: Sibling assignment ambiguous"
node = matches[0]
assert node.lineno == node.end_lineno, "STOP: Assignment layout differs"

old = ast.get_source_segment(src, node)
for expected in (
    "ops.sum(sibling_stack, axis=1)",
    "ops.max(sibling_stack, axis=1)",
    "ops.reshape(remaining[66], [2, 1])",
):
    assert expected in old, f"STOP: Unexpected sibling expression: {expected}"

lines = src.splitlines(keepends=True)
indent = lines[node.lineno - 1][:node.col_offset]

replacement = f"""# {marker}
sibling_sum = ops.reshape(ops.sum(sibling_stack, axis=1), [2, 128])
sibling_max = ops.reshape(ops.max(sibling_stack, axis=1), [2, 128])
sibling_count = ops.cast(ops.reshape(remaining[66], [2, 1]), DType.float32)
sibling = ops.concat([
    sibling_sum / (sibling_count + ops.constant(1e-7, dtype=DType.float32, device=device)),
    sibling_max
], axis=1)"""

new_lines = [indent + line + "\n" for line in replacement.splitlines()]
updated = "".join(lines[:node.lineno - 1] + new_lines + lines[node.end_lineno:])

ast.parse(updated)

backup = p.with_name(p.name + ".before_sibling_pool_fix.bak")
assert not backup.exists(), "STOP: Backup already exists"

backup.write_bytes(p.read_bytes())
p.write_text(updated)

print("SIBLING POOLING FIX: INSTALLED")
print("EXPECTED SIBLING OUTPUT: (2, 256)")
print("BACKUP: PASS")
print("SYNTAX: PASS")
print("DS CODE: UNCHANGED")
print("WORKING MODEL: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
