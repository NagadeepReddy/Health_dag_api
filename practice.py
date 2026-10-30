python3 -B - <<'PY'
from pathlib import Path
import ast
import shutil
import subprocess
import json

dev = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")
backend = dev / "real_max_batch2_backend.py"
candidate = Path(
    "/application1/cta_max_true_batch_dev_20261028/"
    "batch2_candidate/cta_max"
)

P = [
    "podman",
    "--root", "/application1/podman/storage",
    "--runroot", "/run/containers/storage"
]

# Verify actual source files before changing anything.
required = [
    backend,
    candidate / "parallel_transformer_block_2layers.py",
    candidate / "nlp_bert_in_graph.py",
    candidate / "run_batch2_contract.py",
]

for p in required:
    if not p.is_file():
        raise SystemExit(f"STOP: Required file missing: {p}")

# Identify existing container before changing anything.
matches = []

for cid in subprocess.check_output(
    P + ["ps", "-q"], text=True
).split():
    info = json.loads(subprocess.check_output(
        P + ["inspect", cid], text=True
    ))[0]

    mounts = info.get("Mounts", [])
    if any(
        m.get("Source") == str(dev)
        and m.get("Destination") == "/batch2"
        for m in mounts
    ):
        matches.append(cid)

if len(matches) != 1:
    raise SystemExit(
        f"STOP: Expected one Batch-2 container; found {len(matches)}"
    )

src = backend.read_text()

old = (
    '_b2_expected = (_b2_dir if _b2_short == '
    '"parallel_transformer_block_2layers" '
    'else "/batch2/cta_max") + "/" + _b2_short + ".py"'
)

new = '_b2_expected = _b2_dir + "/" + _b2_short + ".py"'

if src.count(old) != 1:
    raise SystemExit("STOP: Unexpected backend version")

updated = src.replace(old, new, 1)
ast.parse(updated)

backup = dev / "real_max_batch2_backend.py.before_unified_helpers"

if backup.exists():
    raise SystemExit("STOP: Backup already exists")

if shutil.disk_usage(dev).free < 20 * 1024 * 1024:
    raise SystemExit("STOP: Insufficient free disk space")

shutil.copy2(backend, backup)
backend.write_text(updated)

print("BOTH HELPER PATHS: CORRECTED")
print("SYNTAX: PASS")

# Import-only validation inside existing container.
code = '''
import importlib.util
from pathlib import Path

p = Path("/batch2/real_max_batch2_backend.py")
spec = importlib.util.spec_from_file_location(
    "cta_batch2_import_check", p
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

assert callable(module.infer_max_batch)
print("BATCH-2 BACKEND IMPORT: PASS")
'''

r = subprocess.run(
    P + [
        "exec", "-i",
        "-e", "PYTHONDONTWRITEBYTECODE=1",
        matches[0],
        "/opt/venv/bin/python", "-B", "-"
    ],
    input=code,
    text=True,
    capture_output=True,
    timeout=30
)

print(r.stdout)
if r.stderr:
    print(r.stderr[-2000:])

print("IMPORT EXIT CODE:", r.returncode)
print("ORIGINAL DS/MAX: UNCHANGED")
print("CONTAINERS RESTARTED: NONE")
PY
