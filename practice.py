cd /application/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

python3 - <<'PY'
from pathlib import Path
import ast, shutil

base = Path("artifacts/v1.168-max/cta_max")
adapter = base / "run_real_sanity_input_adapter.py"
graph = base / "grecbase_fusion_order_correct_max.py"

a = adapter.read_text()
g = graph.read_text()

def replace_once(src, old, new):
    assert src.count(old) == 1, f"STOP: Expected exactly one: {old}"
    return src.replace(old, new, 1)

a2 = replace_once(
    a,
    'add("valid_length", get("vl_in", "v1_in"))',
    'add("valid_length", get("vl_in", "v1_in"))\n'
    '    add("sibling_valid_length", get("sibling_vl_in"))'
)

a2 = replace_once(
    a2,
    'len(labels) == 71',
    'len(labels) == 72'
)

g2 = replace_once(
    g,
    '+ [TensorType(DType.int64, [1], device=device)])',
    '+ [TensorType(DType.int64, [1], device=device) for _ in range(2)])'
)

g2 = replace_once(
    g2,
    'assert len(remaining) == 66',
    'assert len(remaining) == 67'
)

g2 = replace_once(
    g2,
    'ops.reshape(remaining[65], [1, 1])',
    'ops.reshape(remaining[66], [1, 1])'
)

assert 'valid_length = remaining[65]' in g2
assert 'ops.reshape(remaining[66], [1, 1])' in g2

ast.parse(a2)
ast.parse(g2)

for p in (adapter, graph):
    backup = p.with_name(p.name + ".before_sibling_length_mapping_fix")
    assert not backup.exists(), f"STOP: Backup exists: {backup}"

for p in (adapter, graph):
    shutil.copy2(p, p.with_name(p.name + ".before_sibling_length_mapping_fix"))

adapter.write_text(a2)
graph.write_text(g2)

print("FIX APPLIED")
print("Separate Sequence and Sibling lengths")
print("MAX input count: 72")
print("Python syntax: PASS")
print("Both backups preserved")
PY
