python3 -B - <<'PY'
from pathlib import Path
import ast, json, os, shutil, subprocess

dev = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")
backend = dev / "real_max_batch2_backend.py"
candidate = Path(
    "/application1/cta_max_true_batch_dev_20261028/"
    "batch2_candidate/cta_max"
)
graph = candidate / "grecbase_fusion_batch2_draft.py"

P = [
    "podman",
    "--root", "/application1/podman/storage",
    "--runroot", "/run/containers/storage"
]

# Validate source before making changes.
if not backend.is_file() or not graph.is_file():
    raise SystemExit("STOP: Backend or corrected graph missing")

source = backend.read_text()
tree = ast.parse(source)

assignments = [
    n for n in tree.body
    if isinstance(n, ast.Assign)
    and len(n.targets) == 1
    and isinstance(n.targets[0], ast.Name)
    and n.targets[0].id == "_cta_directory"
]

if len(assignments) != 1:
    raise SystemExit("STOP: Unexpected graph directory assignment")

node = assignments[0]
old_value = ast.literal_eval(node.value)

if old_value not in ("/batch2/cta_max", str(candidate)):
    raise SystemExit("STOP: Unexpected current graph directory")

# Find the existing development container.
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
    raise SystemExit("STOP: Expected one existing Batch-2 container")

def run_container(code):
    return subprocess.run(
        P + [
            "exec", "-i",
            "-e", "PYTHONDONTWRITEBYTECODE=1",
            matches[0], "/opt/venv/bin/python", "-B", "-"
        ],
        input=code,
        text=True,
        capture_output=True,
        timeout=45
    )

probe = run_container(
    "from pathlib import Path\n"
    f"assert Path({str(graph)!r}).is_file()\n"
    "print('CORRECTED GRAPH VISIBLE: PASS')\n"
)

if probe.returncode:
    print(probe.stderr[-1500:])
    raise SystemExit("STOP: Candidate graph not visible inside container")

print(probe.stdout.strip())

# Replace precisely the verified assignment, not other paths.
if old_value != str(candidate):
    lines = source.splitlines(keepends=True)
    index = node.lineno - 1
    old_line = lines[index]

    if old_line.strip() != '_cta_directory = "/batch2/cta_max"':
        raise SystemExit("STOP: Unexpected assignment format")

    lines[index] = old_line.replace(
        '"/batch2/cta_max"', repr(str(candidate)), 1
    )
    updated = "".join(lines)
    ast.parse(updated)

    backup = dev / "real_max_batch2_backend.py.before_graph_directory_fix"

    if backup.exists():
        raise SystemExit("STOP: Backup exists; no changes made")

    if shutil.disk_usage(dev).free < 20 * 1024 * 1024:
        raise SystemExit("STOP: Insufficient free disk space")

    shutil.copy2(backend, backup)

    temporary = dev / ".cta_graph_directory_fix.tmp"
    if temporary.exists():
        raise SystemExit("STOP: Temporary file already exists")

    try:
        with temporary.open("x") as f:
            f.write(updated)
        os.chmod(temporary, backend.stat().st_mode)
        os.replace(temporary, backend)
    finally:
        if temporary.exists():
            temporary.unlink()

    print("GRAPH DIRECTORY FIX: INSTALLED")
else:
    print("GRAPH DIRECTORY FIX: ALREADY INSTALLED")

ast.parse(backend.read_text())
print("SYNTAX: PASS")

# Test only the repaired backend import.
smoke = """
import importlib.util
from pathlib import Path

p = Path("/batch2/real_max_batch2_backend.py")
spec = importlib.util.spec_from_file_location("cta_batch2_check", p)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

assert callable(module.infer_max_batch)
print("BATCH-2 BACKEND IMPORT: PASS")
"""

result = run_container(smoke)
print(result.stdout)

if result.stderr:
    print(result.stderr[-2500:])

print("IMPORT EXIT CODE:", result.returncode)
print("ORIGINAL DS/MAX: UNCHANGED")
print("CONTAINERS RESTARTED: NONE")
PY
