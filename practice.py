python3 -B - <<'PY'
from pathlib import Path
import ast, json, shutil, subprocess

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

required = [
    "grecbase_fusion_batch2_draft.py",
    "grecbase_fusion_full_head_72_max.py",
    "parallel_transformer_block_2layers.py",
    "nlp_bert_in_graph.py",
    "run_batch2_contract.py"
]

if not backend.is_file():
    raise SystemExit("STOP: Development backend missing")

missing = [f for f in required if not (candidate / f).is_file()]
if missing:
    raise SystemExit(f"STOP: Candidate files missing: {missing}")

matches = []
for cid in subprocess.check_output(P + ["ps", "-q"], text=True).split():
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
    raise SystemExit(f"STOP: Expected one existing Batch-2 container; found {len(matches)}")

cid = matches[0]

probe = """
from pathlib import Path
p = Path("/application1/cta_max_true_batch_dev_20261028/batch2_candidate/cta_max")
names = [
    "grecbase_fusion_batch2_draft.py",
    "grecbase_fusion_full_head_72_max.py",
    "parallel_transformer_block_2layers.py",
    "nlp_bert_in_graph.py",
    "run_batch2_contract.py"
]
missing = [name for name in names if not (p / name).is_file()]
print("CONTAINER CANDIDATE MISSING:", missing, flush=True)
raise SystemExit(1 if missing else 0)
"""

def in_container(code):
    return subprocess.run(
        P + [
            "exec", "-i", "-e", "PYTHONDONTWRITEBYTECODE=1",
            cid, "/opt/venv/bin/python", "-B", "-"
        ],
        input=code, text=True, capture_output=True, timeout=30
    )

r = in_container(probe)
print(r.stdout)
if r.returncode:
    print(r.stderr[-1500:])
    raise SystemExit("STOP: Candidate not fully visible inside container")

src = backend.read_text()
lines = src.splitlines(keepends=True)

start = next(
    (i for i, line in enumerate(lines)
     if "_cta_candidate = next((" in line),
    None
)

if start is None:
    raise SystemExit("STOP: Candidate selector missing")

end = next(
    (i for i in range(start + 1, min(start + 15, len(lines)))
     if "), None)" in lines[i]),
    None
)

if end is None:
    raise SystemExit("STOP: Selector structure unexpected")

block = lines[start:end + 1]

old_name = '_cta_Path("/batch2/cta_max")'
new_name = f'_cta_Path("{candidate}")'

a = [i for i, line in enumerate(block) if old_name in line]
b = [i for i, line in enumerate(block) if new_name in line]

if len(a) != 1 or len(b) != 1:
    raise SystemExit("STOP: Unexpected candidate definitions")

if a[0] > b[0]:
    print("CANDIDATE PRIORITY: ALREADY CORRECT")
else:
    if b[0] != a[0] + 1:
        raise SystemExit("STOP: Candidate entries not adjacent")

    block[a[0]], block[b[0]] = block[b[0]], block[a[0]]
    updated = "".join(lines[:start] + block + lines[end + 1:])
    ast.parse(updated)

    backup = dev / "real_max_batch2_backend.py.before_candidate_priority_fix"

    if backup.exists():
        raise SystemExit("STOP: Backup already exists")

    if shutil.disk_usage(dev).free < 20 * 1024 * 1024:
        raise SystemExit("STOP: Insufficient disk space")

    shutil.copy2(backend, backup)
    backend.write_text(updated)
    print("CORRECTED GRAPH PRIORITY: INSTALLED")

smoke = """
import importlib.util
from pathlib import Path

p = Path("/batch2/real_max_batch2_backend.py")
spec = importlib.util.spec_from_file_location("cta_batch2_check", p)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

assert callable(module.infer_max_batch)
print("BATCH-2 BACKEND IMPORT: PASS", flush=True)
"""

r = in_container(smoke)
print(r.stdout)
if r.stderr:
    print(r.stderr[-2000:])

print("IMPORT EXIT CODE:", r.returncode)
print("ORIGINAL DS/MAX: UNCHANGED")
print("CONTAINERS RESTARTED: NONE")
PY
