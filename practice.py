python3 -B - <<'PY'
from pathlib import Path
import ast, hashlib, os, re, shutil

root = Path('/application1')
repo = root / 'sajjna8/rt-pzaas-cta-offers-v1'
native = repo / 'artifacts/v1.168-max/maxserve_cta_extension'
dev = root / 'CTA_MAX_TRUE_BATCH2_DEV_20261029'
source = dev / 'native_batch2'
target = dev / 'native_batch2_release_candidate'
tmp = dev / '.native_batch2_release_candidate_build'

required = [
    native / 'cta_worker_adapter.py',
    native / 'cta_native_scheduler.py',
    native / 'cta_scheduler_factory.py',
    native / 'cta_worker_registration.py',
    source / 'cta_worker_adapter.py',
    source / 'cta_native_scheduler.py',
    dev / 'real_max_batch2_backend.py',
    repo / 'artifacts/v1.168/core-artifact/pipeline.py'
]

for p in required:
    if not p.is_file() or p.is_symlink():
        raise SystemExit('STOP: Missing source: ' + str(p))

if target.exists() or tmp.exists():
    raise SystemExit('STOP: Staging directory already exists')

if any(p.is_symlink() for p in native.rglob('*')):
    raise SystemExit('STOP: Native source contains symlinks')

if shutil.disk_usage(dev).free < 50 * 1024 * 1024:
    raise SystemExit('STOP: Insufficient disk space')

def names(p):
    tree = ast.parse(p.read_text())
    return {
        n.name for n in tree.body
        if isinstance(n, (ast.ClassDef, ast.FunctionDef))
    }

if not (
    names(native / 'cta_worker_adapter.py')
    & names(source / 'cta_worker_adapter.py')
):
    raise SystemExit('STOP: Adapter class names differ')

for p in (native / 'cta_native_scheduler.py',
          source / 'cta_native_scheduler.py'):
    if 'CTANativeScheduler' not in names(p):
        raise SystemExit('STOP: Scheduler contract differs')

adapter_tree = ast.parse(
    (source / 'cta_worker_adapter.py').read_text()
)

if not any(
    isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    and n.name == 'predict_batch'
    for n in ast.walk(adapter_tree)
):
    raise SystemExit('STOP: Development predict_batch missing')

if 'CTA_NATIVE_BATCH_DISPATCH_V1' not in (
    source / 'cta_native_scheduler.py'
).read_text():
    raise SystemExit('STOP: Batch dispatch unavailable')

protected = [
    native / 'cta_worker_adapter.py',
    native / 'cta_native_scheduler.py',
    native / 'cta_scheduler_factory.py',
    native / 'cta_worker_registration.py',
    repo / 'artifacts/v1.168/core-artifact/pipeline.py'
]

def hashes():
    return {
        str(p): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in protected
    }

before = hashes()

try:
    pkg = tmp / 'maxserve_cta_extension'

    shutil.copytree(
        native, pkg,
        ignore=shutil.ignore_patterns('__pycache__', '*.pyc')
    )

    for name in ('cta_worker_adapter.py',
                 'cta_native_scheduler.py'):
        shutil.copy2(source / name, pkg / name)

    # Only the staged copies receive Batch-2 defaults.
    for name in ('cta_scheduler_factory.py',
                 'cta_native_scheduler.py'):
        p = pkg / name
        content = p.read_text()

        updated, count = re.subn(
            r'(\bmax_items_per_iteration\s*=\s*)1\b',
            r'\g<1>2',
            content
        )

        if count != 1:
            raise RuntimeError(
                f'{name}: Unexpected batch-limit definition'
            )

        ast.parse(updated)
        p.write_text(updated)

    for p in pkg.rglob('*.py'):
        ast.parse(p.read_text())

    adapter_code = (pkg / 'cta_worker_adapter.py').read_text()
    scheduler_code = (pkg / 'cta_native_scheduler.py').read_text()

    if ('predict_batch' not in adapter_code
            or 'batch_fn(' not in scheduler_code):
        raise RuntimeError('Batch wiring missing')

    if hashes() != before:
        raise RuntimeError('Original source changed unexpectedly')

    os.replace(tmp, target)

except BaseException:
    if tmp.exists():
        shutil.rmtree(tmp)
    raise

print('NATIVE BATCH-2 STAGING: PASS')
print('CANDIDATE:', target / 'maxserve_cta_extension')
print('BATCH ADAPTER: STAGED')
print('BATCH SCHEDULER: STAGED')
print('STAGED BATCH SIZE: 2')
print('ALL PYTHON SYNTAX: PASS')
print('ORIGINAL DS/MAX: UNCHANGED')
print('WORKING NATIVE RELEASE: UNCHANGED')
print('CONTAINERS RESTARTED: NONE')
print('LIVE HTTP BATCHING: NOT YET VALIDATED')
PY
