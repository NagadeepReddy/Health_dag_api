python3 -B - <<'PY'
from pathlib import Path
import ast, json, os, shutil, subprocess

base = Path('/application1')
dev = base / 'CTA_MAX_TRUE_BATCH2_DEV_20261029'
backend = dev / 'real_max_batch2_backend.py'
candidate = base / 'cta_max_true_batch_dev_20261028/batch2_candidate/cta_max'
verified_graph = candidate / 'grecbase_fusion_full_head_72_max.py'

P = [
    'podman',
    '--root', '/application1/podman/storage',
    '--runroot', '/run/containers/storage'
]

if not backend.is_file() or not verified_graph.is_file():
    raise SystemExit('STOP: Backend or prior CPU-pass graph missing')

src = backend.read_text()
ast.parse(src)

old = '"/grecbase_fusion_batch2_draft.py"'
new = '"/grecbase_fusion_full_head_72_max.py"'

if (src.count(old) + src.count(new) != 1 or
        'from cta_max.grecbase_fusion_full_head_72_max import' not in src):
    raise SystemExit('STOP: Backend differs from recorded version; unchanged')

matched = []
for cid in subprocess.check_output(P + ['ps', '-q'], text=True).split():
    info = json.loads(
        subprocess.check_output(P + ['inspect', cid], text=True)
    )[0]
    if any(
        m.get('Destination') == '/batch2'
        and m.get('Source') == str(dev)
        for m in info.get('Mounts', [])
    ):
        matched.append(cid)

if len(matched) != 1:
    raise SystemExit('STOP: Existing Batch-2 container unavailable')

ram = int(next(
    line.split()[1]
    for line in Path('/proc/meminfo').read_text().splitlines()
    if line.startswith('MemAvailable:')
)) // 1024

print('AVAILABLE RAM MB:', ram, flush=True)

if ram < 12000 or shutil.disk_usage(dev).free < 20 * 1024 * 1024:
    raise SystemExit('STOP: Insufficient host resources')

def run(code, timeout):
    return subprocess.run(
        P + [
            'exec', '-i', '-w', '/workspace',
            '-e', 'PYTHONDONTWRITEBYTECODE=1',
            '-e', 'PYTHONPATH=/batch2:/workspace/artifacts/v1.168-max',
            matched[0], '/opt/venv/bin/python', '-B', '-'
        ],
        input=code, text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout
    )

preflight = r'''
import importlib.util
from pathlib import Path
import cta_max

p = Path(
    '/application1/cta_max_true_batch_dev_20261028/'
    'batch2_candidate/cta_max/grecbase_fusion_full_head_72_max.py'
)

assert p.is_file()
cta_max.__path__.insert(0, str(p.parent))

spec = importlib.util.spec_from_file_location(
    'cta_max._cpu_passed_graph_preflight', p
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

assert callable(
    getattr(mod, 'build_grecbase_fusion_graph_order_correct', None)
)

print('CPU-PASSED GRAPH BUILDER: AVAILABLE', flush=True)
'''

r = run(preflight, 45)
print(r.stdout[-2000:])

if r.returncode:
    raise SystemExit('STOP: CPU graph compatibility failed; no changes')

if src.count(old) == 1:
    updated = src.replace(old, new, 1)
    ast.parse(updated)

    backup = backend.with_name(
        backend.name + '.before_cpu_passed_graph_reuse'
    )
    tmp = dev / '.real_max_batch2_graph.tmp'

    if backup.exists() or tmp.exists():
        raise SystemExit('STOP: Backup or temporary file already exists')

    shutil.copy2(backend, backup)

    try:
        with tmp.open('x') as stream:
            stream.write(updated)
        os.chmod(tmp, backend.stat().st_mode)
        os.replace(tmp, backend)
    finally:
        if tmp.exists():
            tmp.unlink()

    print('ISOLATED BACKEND: CPU-PASSED GRAPH SELECTED', flush=True)
else:
    print('CPU-PASSED GRAPH: ALREADY SELECTED', flush=True)

smoke = r'''
import importlib.util
from pathlib import Path

p = Path('/batch2/real_max_batch2_backend.py')
spec = importlib.util.spec_from_file_location(
    'cta_batch2_verified_import', p
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

expected = Path(
    '/application1/cta_max_true_batch_dev_20261028/'
    'batch2_candidate/cta_max/grecbase_fusion_full_head_72_max.py'
)

assert Path(mod._cta_module.__file__).resolve() == expected.resolve()
assert callable(mod.infer_max_batch)

print('BATCH-2 VERIFIED GRAPH IMPORT: PASS', flush=True)
'''

r = run(smoke, 45)
print(r.stdout[-2500:])

if r.returncode:
    raise SystemExit('STOP: Backend import failed; MAX not executed')

execution = r'''
import sys, os, ast, json, inspect
from pathlib import Path

root = Path('/workspace')
core = root / 'artifacts/v1.168/core-artifact'
maxroot = root / 'artifacts/v1.168-max'

sys.path[:0] = [str(core), str(maxroot), '/batch2']

spawn = maxroot / 'maxserve_cta_extension/cta_spawn_worker.py'

if spawn.is_file():
    for node in ast.walk(ast.parse(spawn.read_text())):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != 'setdefault' or len(node.args) < 2:
            continue
        try:
            key = ast.literal_eval(node.args[0])
            val = ast.literal_eval(node.args[1])
        except (TypeError, SyntaxError, ValueError):
            continue
        if key in ('modelId', 'expThrottleLabel') and isinstance(val, str):
            os.environ.setdefault(key, val)

import pipeline as original

assert Path(original.__file__).resolve() == (core / 'pipeline.py').resolve()

import cta_max

repo = str(maxroot / 'cta_max')
if repo not in cta_max.__path__:
    cta_max.__path__.append(repo)

from cta_max.live_cta_pipeline_bridge import attach_max
from native_batch2 import cta_worker_adapter as mod

classes = [
    c for _, c in inspect.getmembers(mod, inspect.isclass)
    if c.__module__ == mod.__name__
    and callable(getattr(c, 'predict_batch', None))
]

assert len(classes) == 1, 'Batch adapter unavailable'

adapter = classes[0](original.pipeline, attach_max)

fixtures = [
    maxroot / 'test-results/cta_max_tiles_smoketest_input.json',
    maxroot / 'cta_native_adjusted_sanity_input.json'
]

assert all(f.is_file() for f in fixtures), 'CTA fixtures missing'

bodies = [json.loads(f.read_text()) for f in fixtures]
assert all(isinstance(x, dict) for x in bodies)

print('REAL CTA JSON BATCH-2: START', flush=True)

responses = adapter.predict_batch(bodies)

assert isinstance(responses, (list, tuple))
assert len(responses) == 2, 'Response count mismatch'

for index, response in enumerate(responses, 1):
    assert isinstance(response, dict)
    assert 'error' not in response
    assert isinstance(response.get('jsonData'), dict)
    assert 'prediction' in response['jsonData']
    json.dumps(response, allow_nan=False)
    print(f'CTA RESPONSE {index}: VALID', flush=True)

print('REAL CTA JSON BATCH-2: PASS', flush=True)
'''

try:
    r = run(execution, 300)
    print(r.stdout[-8000:])
    print('JSON BATCH-2 EXIT CODE:', r.returncode)
except subprocess.TimeoutExpired as e:
    output = e.stdout or b''
    if isinstance(output, bytes):
        output = output.decode(errors='replace')
    print(output[-4000:])
    print('STOP: JSON Batch-2 exceeded 300 seconds')

print('ORIGINAL DS/MAX: UNCHANGED')
print('CONTAINERS RESTARTED: NONE')
PY
