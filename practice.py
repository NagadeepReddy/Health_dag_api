python3 -B - <<'PY'
from pathlib import Path
import ast, json, shutil, subprocess, os

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

# 1. Validate files and existing container BEFORE editing.
if not backend.is_file():
    raise SystemExit("STOP: Backend missing")

for name in (
    "grecbase_fusion_batch2_draft.py",
    "grecbase_fusion_full_head_72_max.py",
    "parallel_transformer_block_2layers.py",
    "nlp_bert_in_graph.py",
    "run_batch2_contract.py",
):
    if not (candidate / name).is_file():
        raise SystemExit("STOP: Missing candidate file: " + name)

matches = []
for cid in subprocess.check_output(
    P + ["ps", "-q"], text=True
).split():
    info = json.loads(
        subprocess.check_output(P + ["inspect", cid], text=True)
    )[0]
    if any(
        m.get("Source") == str(dev)
        and m.get("Destination") == "/batch2"
        for m in info.get("Mounts", [])
    ):
        matches.append(cid)

if len(matches) != 1:
    raise SystemExit("STOP: Existing Batch-2 container unavailable")

# 2. Change ONLY path values, preserving the original commas.
source = backend.read_text()
lines = source.splitlines(keepends=True)

positions = [
    i for i, line in enumerate(lines)
    if line.strip() == "_cta_candidate = next(("
]

if len(positions) != 1:
    raise SystemExit("STOP: Unexpected candidate selector")

i = positions[0]
first = '_cta_Path("/batch2/cta_max"),'
second = f'_cta_Path("{candidate}")'

if (lines[i+2].strip() == second + ","
        and lines[i+3].strip() == '_cta_Path("/batch2/cta_max")'):
    print("CANDIDATE ORDER: ALREADY CORRECT")
elif (lines[i+2].strip() == first
      and lines[i+3].strip() == second):
    lines[i+2] = lines[i+2].replace(
        '"/batch2/cta_max"', f'"{candidate}"'
    )
    lines[i+3] = lines[i+3].replace(
        f'"{candidate}"', '"/batch2/cta_max"'
    )

    updated = "".join(lines)
    ast.parse(updated)

    backup = backend.with_name(
        backend.name + ".before_safe_candidate_order"
    )

    if backup.exists():
        raise SystemExit("STOP: Backup already exists")

    if shutil.disk_usage(dev).free < 20 * 1024 * 1024:
        raise SystemExit("STOP: Low disk space")

    shutil.copy2(backend, backup)

    temp = dev / ".batch2_backend_order_update.tmp"
    if temp.exists():
        raise SystemExit("STOP: Temporary file exists")

    try:
        with temp.open("x") as f:
            f.write(updated)
        os.replace(temp, backend)
    finally:
        if temp.exists():
            temp.unlink()

    print("CANDIDATE PATH ORDER: CORRECTED")
else:
    raise SystemExit("STOP: Unexpected selector format")

ast.parse(backend.read_text())
print("HOST SYNTAX: PASS")

# 3. Import-only test inside the existing container.
smoke = '''
import importlib.util
from pathlib import Path

p = Path("/batch2/real_max_batch2_backend.py")
spec = importlib.util.spec_from_file_location(
    "cta_batch2_import_validation", p
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

expected = Path(
    "/application1/cta_max_true_batch_dev_20261028/"
    "batch2_candidate/cta_max"
)

assert Path(module._cta_candidate).resolve() == expected.resolve()
assert callable(module.infer_max_batch)

print("CORRECTED GRAPH SELECTED: PASS")
print("BATCH-2 BACKEND IMPORT: PASS")
'''

r = subprocess.run(
    P + [
        "exec", "-i",
        "-e", "PYTHONDONTWRITEBYTECODE=1",
        matches[0],
        "/opt/venv/bin/python", "-B", "-"
    ],
    input=smoke,
    text=True,
    capture_output=True,
    timeout=30
)

print(r.stdout)
if r.stderr:
    print(r.stderr[-2500:])

print("IMPORT EXIT CODE:", r.returncode)
print("ORIGINAL DS/MAX: UNCHANGED")
print("CONTAINERS RESTARTED: NONE")
PY
