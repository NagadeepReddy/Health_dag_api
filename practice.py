python3 -B - <<'PY'
from pathlib import Path
import ast, json, re, shutil, subprocess, os

base = Path('/application1')
dev = base / 'CTA_MAX_TRUE_BATCH2_DEV_20261029'
candidate = base / 'cta_max_true_batch_dev_20261028/batch2_candidate/cta_max'
graph = candidate / 'grecbase_fusion_full_head_72_max.py'
backend = dev / 'real_max_batch2_backend.py'
dest = candidate / 'sibling_context_max_batch2_fix.py'

P = ['podman', '--root', '/application1/podman/storage',
     '--runroot', '/run/containers/storage']

if not all(p.is_file() and not p.is_symlink() for p in (graph, backend)):
    raise SystemExit('STOP: Known graph/backend missing')

if (str(candidate) not in backend.read_text()
        or 'grecbase_fusion_full_head_72_max.py' not in backend.read_text()):
    raise SystemExit('STOP: Backend is not using the verified graph')

# Reuse the earlier Batch-2 sibling fix.
known = [
    dest,
    dev / 'sibling_context_max_batch2_fix.py',
    dev / 'cta_max/sibling_context_max_batch2_fix.py',
    dev / 'native_batch2/sibling_context_max_batch2_fix.py',
    candidate / 'sibling_context_max.py'
]

usable = []
for p in known:
    if p.is_file() and not p.is_symlink():
        s = p.read_text()
        if ('def sibling_context_forward' in s
                and re.search(r'\[\s*2\s*,\s*128\s*\]', s)):
            ast.parse(s)
            usable.append(p)

if not usable:
    raise SystemExit(
        'STOP: Existing corrected sibling helper not found. No changes made.'
    )

src = usable[0]
print('REUSING EXISTING SIBLING FIX:', src, flush=True)

contents = graph.read_text()
tree = ast.parse(contents)

imports = [
    n for n in ast.walk(tree)
    if isinstance(n, ast.ImportFrom)
    and any(a.name == 'sibling_context_forward' for a in n.names)
]

allowed = (
    'cta_max.sibling_context_max',
    'sibling_context_max',
    'cta_max.sibling_context_max_batch2_fix'
)

if len(imports) != 1 or imports[0].module not in allowed:
    raise SystemExit('STOP: Graph import differs from expected source')

node = imports[0]
lines = contents.splitlines(keepends=True)
old = lines[node.lineno - 1]

if node.end_lineno != node.lineno or not old.lstrip().startswith('from '):
    raise SystemExit('STOP: Unexpected import structure')

new = old.replace(
    'sibling_context_max import ',
    'sibling_context_max_batch2_fix import ', 1
)

if new == old and 'sibling_context_max_batch2_fix import' not in old:
    raise SystemExit('STOP: Expected sibling import missing')

lines[node.lineno - 1] = new
updated = ''.join(lines)
ast.parse(updated)

ids = []
for cid in subprocess.check_output(P + ['ps', '-q'], text=True).split():
    info = json.loads(
        subprocess.check_output(P + ['inspect', cid], text=True)
    )[0]
    if any(
        m.get('Source') == str(dev)
        and m.get('Destination') == '/batch2'
        for m in info.get('Mounts', [])
    ):
        ids.append(cid)

if len(ids) != 1:
    raise SystemExit('STOP: Existing development container unavailable')

ram = int(next(
    x.split()[1] for x in Path('/proc/meminfo').read_text().splitlines()
    if x.startswith('MemAvailable:')
)) // 1024

print('AVAILABLE RAM MB:', ram, flush=True)

if shutil.disk_usage(candidate).free < 20 * 1024 * 1024 or ram < 12000:
    raise SystemExit('STOP: Insufficient resources')

# Change only the isolated Batch-2 candidate.
if src != dest and not dest.exists():
    shutil.copy2(src, dest)
    print('CORRECTED SIBLING HELPER: STAGED', flush=True)
elif src != dest and dest.exists():
    raise SystemExit('STOP: Existing helper destination conflict')

if updated != contents:
    backup = graph.with_name(graph.name + '.before_existing_sibling_fix')
    tmp = graph.with_name('.batch2_graph_sibling_fix.tmp')

    if backup.exists() or tmp.exists():
        raise SystemExit('STOP: Existing backup/temp file')

    shutil.copy2(graph, backup)

    try:
        with tmp.open('x') as f:
            f.write(updated)
        os.chmod(tmp, graph.stat().st_mode)
        os.replace(tmp, graph)
    finally:
        if tmp.exists():
            tmp.unlink()

print('ISOLATED GRAPH IMPORT: PASS', flush=True)

def run(code, timeout):
    return subprocess.run(
        P + [
            'exec', '-i', '-w', '/workspace',
            '-e', 'PYTHONDONTWRITEBYTECODE=1',
            '-e', 'TMPDIR=/tmp',
            '-e', 'PYTHONPATH=/batch2:/workspace/artifacts/v1.168-max',
            ids[0], '/opt/venv/bin/python', '-B', '-'
        ],
        input=code, text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout
    )

# Verify that the graph actually uses the Batch-2 sibling helper.
smoke = '''
import importlib.util
from pathlib import Path

p = Path('/batch2/real_max_batch2_backend.py')
spec = importlib.util.spec_from_file_location('cta_batch2_reuse_check', p)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

assert callable(mod.infer_max_batch)
assert mod._cta_module.sibling_context_forward.__module__.endswith(
    '.sibling_context_max_batch2_fix'
)

print('CORRECTED SIBLING IMPORT: PASS', flush=True)
'''

r = run(smoke, 45)
print(r.stdout[-2500:])

if r.returncode:
    raise SystemExit('STOP: Import failed. MAX not executed.')

# Run the real CTA JSON integration.
execution = '''
import sys, os, ast, json, inspect
from pathlib import Path

root = Path('/workspace')
core = root / 'artifacts/v1.168/core-artifact'
maxroot = root / 'artifacts/v1.168-max'

sys.path[:0] = [str(core), str(maxroot), '/batch2']

spawn = maxroot / 'maxserve_cta_extension/cta_spawn_worker.py'

if spawn.is_file():
    for n in ast.walk(ast.parse(spawn.read_text())):
        if (isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute)
            and n.func.attr == 'setdefault'
            and len(n.args) >= 2):
            try:
                key = ast.literal_eval(n.args[0])
                val = ast.literal_eval(n.args[1])
            except (TypeError, ValueError, SyntaxError):
                continue
            if key in ('modelId', 'expThrottleLabel') and isinstance(val, str):
                os.environ.setdefault(key, val)

import pipeline as original
assert Path(original.__file__).resolve() == (core / 'pipeline.py').resolve()

import cta_max
repo_pkg = str(maxroot / 'cta_max')
if repo_pkg not in cta_max.__path__:
    cta_max.__path__.append(repo_pkg)

from cta_max.live_cta_pipeline_bridge import attach_max
from native_batch2 import cta_worker_adapter as mod

classes = [
    c for _, c in inspect.getmembers(mod, inspect.isclass)
    if c.__module__ == mod.__name__
    and callable(getattr(c, 'predict_batch', None))
]
assert len(classes) == 1

adapter = classes[0](original.pipeline, attach_max)

fixtures = [
    maxroot / 'test-results/cta_max_tiles_smoketest_input.json',
    maxroot / 'cta_native_adjusted_sanity_input.json'
]
assert all(p.is_file() for p in fixtures)

bodies = [json.loads(p.read_text()) for p in fixtures]

print('REAL CTA JSON BATCH-2: START', flush=True)
responses = adapter.predict_batch(bodies)

assert isinstance(responses, (list, tuple)) and len(responses) == 2

for i, response in enumerate(responses, 1):
    assert isinstance(response, dict)
    assert 'error' not in response
    assert isinstance(response.get('jsonData'), dict)
    assert 'prediction' in response['jsonData']
    json.dumps(response, allow_nan=False)
    print(f'CTA RESPONSE {i}: PASS', flush=True)

print('REAL CTA JSON BATCH-2: PASS', flush=True)
'''

try:
    r = run(execution, 300)
    print(r.stdout[-6500:])
    print('JSON BATCH-2 EXIT CODE:', r.returncode)
except subprocess.TimeoutExpired as e:
    output = e.stdout or b''
    if isinstance(output, bytes):
        output = output.decode(errors='replace')
    print(output[-3500:])
    print('STOP: JSON test exceeded 300 seconds')

print('ORIGINAL DS/MAX: UNCHANGED')
print('CONTAINERS RESTARTED: NONE')
PY
