python3 -B - <<'PY'
from pathlib import Path
import ast, json, os, shutil, subprocess, inspect

base = Path('/application1')
dev = base / 'CTA_MAX_TRUE_BATCH2_DEV_20261029'
candidate = base / 'cta_max_true_batch_dev_20261028/batch2_candidate/cta_max'
repo = base / 'sajjna8/rt-pzaas-cta-offers-v1'

graph = candidate / 'grecbase_fusion_full_head_72_max.py'
backend = dev / 'real_max_batch2_backend.py'
corrected_main = candidate / 'main_context_max.py'
original_main = repo / 'artifacts/v1.168-max/cta_max/main_context_max.py'
aliased_main = candidate / 'main_context_max_batch2_verified.py'

P = [
    'podman',
    '--root', '/application1/podman/storage',
    '--runroot', '/run/containers/storage'
]

# Verify the existing corrected candidate.
for p in (graph, backend, corrected_main, original_main):
    if not p.is_file() or p.is_symlink():
        raise SystemExit('STOP: Required source missing or symlink: ' + str(p))

if corrected_main.read_bytes() == original_main.read_bytes():
    raise SystemExit('STOP: Candidate context is identical to original')

helper_tree = ast.parse(corrected_main.read_text())
if not any(
    isinstance(n, ast.FunctionDef) and n.name == 'main_context_forward'
    for n in helper_tree.body
):
    raise SystemExit('STOP: Corrected context function unavailable')

if (
    str(candidate) not in backend.read_text()
    or 'grecbase_fusion_full_head_72_max.py' not in backend.read_text()
):
    raise SystemExit('STOP: Backend is not selecting the known graph')

# Identify precisely the import that is loading the original helper.
source = graph.read_text()
tree = ast.parse(source)
imports = [
    n for n in ast.walk(tree)
    if isinstance(n, ast.ImportFrom)
    and n.module in (
        'cta_max.main_context_max',
        'cta_max.main_context_max_batch2_verified'
    )
    and any(a.name == 'main_context_forward' for a in n.names)
]

if len(imports) != 1 or imports[0].end_lineno != imports[0].lineno:
    raise SystemExit('STOP: Unexpected context import; graph unchanged')

lines = source.splitlines(keepends=True)
node = imports[0]

if node.module == 'cta_max.main_context_max':
    lines[node.lineno - 1] = lines[node.lineno - 1].replace(
        'cta_max.main_context_max',
        'cta_max.main_context_max_batch2_verified',
        1
    )

updated = ''.join(lines)
ast.parse(updated)

if aliased_main.exists():
    if (
        aliased_main.is_symlink()
        or aliased_main.read_bytes() != corrected_main.read_bytes()
    ):
        raise SystemExit('STOP: Existing corrected helper conflicts')

# Use only the already-running development container.
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
    raise SystemExit('STOP: Expected one existing development container')

def run(code, timeout=45):
    return subprocess.run(
        P + [
            'exec', '-i', '-w', '/workspace',
            '-e', 'PYTHONDONTWRITEBYTECODE=1',
            '-e', 'TMPDIR=/tmp',
            '-e', 'PYTHONPATH=/batch2:/workspace/artifacts/v1.168-max',
            ids[0], '/opt/venv/bin/python', '-B', '-'
        ],
        input=code,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout
    )

preflight = f'''
from pathlib import Path
assert Path({str(corrected_main)!r}).is_file()
assert Path({str(graph)!r}).is_file()
assert Path(
    "/workspace/artifacts/v1.168-max/test-results/cta_max_tiles_smoketest_input.json"
).is_file()
assert Path(
    "/workspace/artifacts/v1.168-max/cta_native_adjusted_sanity_input.json"
).is_file()
print("CANDIDATE AND JSON FIXTURES: VISIBLE")
'''

r = run(preflight)
print(r.stdout[-1500:])

if r.returncode:
    raise SystemExit('STOP: Container preflight failed')

if shutil.disk_usage(candidate).free < 20 * 1024 * 1024:
    raise SystemExit('STOP: Insufficient workspace disk')

backup = graph.with_name(
    graph.name + '.before_context_batch2_reuse'
)

if updated != source and backup.exists():
    raise SystemExit('STOP: Existing backup; no overwrite')

# Stage only the corrected development helper.
if not aliased_main.exists():
    shutil.copy2(corrected_main, aliased_main)
    print('CORRECTED CONTEXT HELPER: STAGED', flush=True)

if updated != source:
    shutil.copy2(graph, backup)

    temporary = graph.with_name('.cta_context_import_update.tmp')
    if temporary.exists():
        raise SystemExit('STOP: Temporary file already exists')

    try:
        with temporary.open('x') as f:
            f.write(updated)
        os.chmod(temporary, graph.stat().st_mode)
        os.replace(temporary, graph)
    finally:
        if temporary.exists():
            temporary.unlink()

print('ISOLATED GRAPH CONTEXT IMPORT: CORRECTED', flush=True)

# Verify actual function source, not merely successful import.
smoke = '''
import importlib.util, inspect
from pathlib import Path

p = Path("/batch2/real_max_batch2_backend.py")
spec = importlib.util.spec_from_file_location(
    "cta_batch2_context_check", p
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

assert callable(module.infer_max_batch)

actual = Path(
    inspect.getsourcefile(module._cta_module.main_context_forward)
).resolve()

expected = Path(
    "/application1/cta_max_true_batch_dev_20261028/"
    "batch2_candidate/cta_max/main_context_max_batch2_verified.py"
).resolve()

print("ACTIVE CONTEXT SOURCE:", actual)
assert actual == expected

print("BATCH-2 CORRECTED CONTEXT IMPORT: PASS")
'''

r = run(smoke)
print(r.stdout[-2500:])

if r.returncode:
    raise SystemExit('STOP: Import failed; MAX not executed')

ram = int(next(
    x.split()[1]
    for x in Path('/proc/meminfo').read_text().splitlines()
    if x.startswith('MemAvailable:')
)) // 1024

print('AVAILABLE RAM MB:', ram)

if ram < 12000:
    raise SystemExit('STOP: Insufficient available memory')

# Reuse the same genuine JSON integration test.
execution = r'''
import sys, os, ast, json, inspect
from pathlib import Path

root = Path("/workspace")
core = root / "artifacts/v1.168/core-artifact"
maxroot = root / "artifacts/v1.168-max"

sys.path[:0] = [str(core), str(maxroot), "/batch2"]

spawn = maxroot / "maxserve_cta_extension/cta_spawn_worker.py"

if spawn.is_file():
    for n in ast.walk(ast.parse(spawn.read_text())):
        if not (
            isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute)
            and n.func.attr == "setdefault"
            and len(n.args) >= 2
        ):
            continue
        try:
            key = ast.literal_eval(n.args[0])
            val = ast.literal_eval(n.args[1])
        except (TypeError, ValueError, SyntaxError):
            continue
        if key in ("modelId", "expThrottleLabel") and isinstance(val, str):
            os.environ.setdefault(key, val)

import pipeline as original
assert Path(original.__file__).resolve() == (core / "pipeline.py").resolve()

import cta_max
repo_pkg = str(maxroot / "cta_max")
if repo_pkg not in cta_max.__path__:
    cta_max.__path__.append(repo_pkg)

from cta_max.live_cta_pipeline_bridge import attach_max
from native_batch2 import cta_worker_adapter as mod

classes = [
    c for _, c in inspect.getmembers(mod, inspect.isclass)
    if c.__module__ == mod.__name__
    and callable(getattr(c, "predict_batch", None))
]

assert len(classes) == 1
adapter = classes[0](original.pipeline, attach_max)

fixtures = [
    maxroot / "test-results/cta_max_tiles_smoketest_input.json",
    maxroot / "cta_native_adjusted_sanity_input.json"
]

assert all(p.is_file() for p in fixtures)
bodies = [json.loads(p.read_text()) for p in fixtures]

print("REAL TWO-REQUEST CTA JSON BATCH-2: START", flush=True)
responses = adapter.predict_batch(bodies)

assert isinstance(responses, (list, tuple))
assert len(responses) == 2

for i, response in enumerate(responses, 1):
    assert isinstance(response, dict)
    assert "error" not in response
    assert isinstance(response.get("jsonData"), dict)
    assert "prediction" in response["jsonData"]
    json.dumps(response, allow_nan=False)
    print(f"CTA RESPONSE {i}: PASS", flush=True)

print("REAL CTA JSON BATCH-2: PASS", flush=True)
'''

try:
    r = run(execution, 300)
    print(r.stdout[-7000:])
    print('JSON BATCH-2 EXIT CODE:', r.returncode)

except subprocess.TimeoutExpired as e:
    output = e.stdout or b''
    if isinstance(output, bytes):
        output = output.decode(errors='replace')
    print(output[-3500:])
    print('STOP: JSON execution exceeded 300 seconds')

print('ORIGINAL DS/MAX: UNCHANGED')
print('CONTAINERS RESTARTED: NONE')
PY
