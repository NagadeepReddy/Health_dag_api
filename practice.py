
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
from pathlib import Path
import ast, json, re, shutil, subprocess

base = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")
backend = base / "real_max_batch2_backend.py"
graph = Path(
    "/application1/cta_max_true_batch_dev_20261028/"
    "batch2_candidate/cta_max/"
    "grecbase_fusion_full_head_72_max.py"
)
backup = base / "real_max_batch2_backend.before_graph2.py"

old = "cta_max.grecbase_fusion_order_correct_max"
new = "cta_max.grecbase_fusion_full_head_72_max"
name = "cta-batch2-trace-8766-v2"

def check(ok, message):
    if not ok:
        raise SystemExit("STOP: " + message)

check(backend.is_file(), "Backend missing")
check(graph.is_file(), "Batch-2 graph missing")

source = backend.read_text()
candidate = graph.read_text()
ast.parse(source)
tree = ast.parse(candidate)

builders = [
    n for n in tree.body
    if isinstance(n, ast.FunctionDef)
    and n.name == "build_grecbase_fusion_graph_order_correct"
]
check(len(builders) == 1, "Graph builder mismatch")

check(
    re.search(r"TensorType\(DType\.float32,\s*\[2,\s*256\]", candidate)
    is not None,
    "Graph does not declare batch-2 inputs"
)
check(
    re.search(r"ops\.reshape\(outs,\s*\[2,\s*2048\]\)", candidate)
    is not None,
    "Batch-2 output contract not confirmed"
)

pod = [
    "podman",
    "--root", "/application1/podman/storage",
    "--runroot", "/run/containers/storage",
]

r = subprocess.run(
    pod + ["ps", "-aq"],
    capture_output=True, text=True
)
check(r.returncode == 0, "Cannot verify containers")

ids = r.stdout.split()
check(bool(ids), "No containers found")

r = subprocess.run(
    pod + ["inspect"] + ids,
    capture_output=True, text=True
)
check(r.returncode == 0, "Container inspection failed")

containers = json.loads(r.stdout)
found = False

for container in containers:
    cname = container.get("Name", "").lstrip("/")
    mounts = container.get("Mounts") or []
    shared = any(
        str(m.get("Source", "")) == str(backend)
        for m in mounts
    )
    if cname == name:
        found = True
        check(shared, "Isolated backend mount differs")
        check(
            not container.get("State", {}).get("Running", False),
            "Isolated container running; do not edit live code"
        )
    elif shared and container.get("State", {}).get("Running", False):
        raise SystemExit(
            "STOP: Backend shared with running container " + cname
        )

check(found, "Target isolated container not found")

if new in source:
    print("BATCH-2 GRAPH: ALREADY SELECTED")
else:
    check(source.count(old) == 1, "Expected import differs")
    check(not backup.exists(), "Backup already exists")

    updated = source.replace(old, new, 1)
    ast.parse(updated)

    shutil.copy2(backend, backup)
    backend.write_text(updated)

    check(
        ast.parse(backend.read_text()) is not None,
        "Syntax verification failed"
    )

    print("BATCH-2 GRAPH: SELECTED")
    print("BACKUP: PRESERVED")

print("SYNTAX: PASS")
print("ORIGINAL DS: UNCHANGED")
print("ORIGINAL MAX: NOT RESTARTED")
print("ISOLATED HTTP VALIDATION: PENDING")
PY
