python3 - <<'PY'
from pathlib import Path
import ast
import re

d = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")
src = d / "real_max_batch2_backend.py"
dst = d / "real_max_batch2_backend_cached_candidate.py"

assert src.is_file(), "STOP: Original backend missing"

s = src.read_text()

pattern = r'(?m)^([ \t]*)graph = build_grecbase_fusion_graph_order_correct\(device_ref\)[ \t]*$'
matches = list(re.finditer(pattern, s))
assert len(matches) == 1, "STOP: Unexpected graph builder"

m = matches[0]
indent = m.group(1)

replacement = (
    indent + 'graph = getattr(infer_max_batch, "_max_graph", None)\n'
    + indent + 'if graph is None:\n'
    + indent + '    graph = build_grecbase_fusion_graph_order_correct(device_ref)\n'
    + indent + '    infer_max_batch._max_graph = graph'
)

s = s[:m.start()] + replacement + s[m.end():]

lines = s.splitlines(keepends=True)

starts = [
    i for i, line in enumerate(lines)
    if line.strip() == 'session = getattr(infer_max_batch, "_max_session", None)'
]

ends = [
    i for i, line in enumerate(lines)
    if 'print("EXECUTING REAL CTA INPUTS...' in line
]

assert len(starts) == len(ends) == 1, "STOP: Cache boundaries differ"

a, b = starts[0], ends[0]
assert a < b, "STOP: Invalid cache block"

base = re.match(r'[ \t]*', lines[a]).group()

assert re.match(r'[ \t]*', lines[b]).group() == base, \
    "STOP: Execution indentation differs"

block = lines[a:b]
wrapped = [
    base + 'model = getattr(infer_max_batch, "_max_model", None)\n',
    base + 'if model is None:\n'
]

wrapped += [
    '    ' + line if line.strip() else line
    for line in block
]

lines[a:b] = wrapped
patched = ''.join(lines)

ast.parse(patched, filename=str(dst))

assert patched != src.read_text(), "STOP: No changes"

if dst.exists():
    assert dst.read_text() == patched, \
        "STOP: Existing candidate differs"
else:
    dst.write_text(patched)

print("GRAPH CACHE: STAGED")
print("CHECKPOINT RELOAD BYPASS: STAGED")
print("MODEL REUSE: STAGED")
print("SYNTAX: PASS")
print("ORIGINAL BACKEND: UNCHANGED")
print("WORKING NATIVE SERVER: UNCHANGED")
print("OPTIMIZED CANDIDATE:", dst)
PY
