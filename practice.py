python3 -B - <<'PY'
from pathlib import Path
import ast, io, tokenize, json, os, shutil, subprocess, tempfile

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

# Check source and existing container first.
if not backend.is_file() or not graph.is_file():
    raise SystemExit("STOP: Existing backend or corrected graph missing")

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

cid = matches[0]

def container_run(code):
    return subprocess.run(
        P + [
            "exec", "-i",
            "-e", "PYTHONDONTWRITEBYTECODE=1",
            cid, "/opt/venv/bin/python", "-B", "-"
        ],
        input=code,
        text=True,
        capture_output=True,
        timeout=45
    )

probe = container_run(
    "from pathlib import Path\n"
    f"assert Path({str(graph)!r}).is_file()\n"
    "print('CORRECTED GRAPH VISIBLE: PASS')\n"
)

print(probe.stdout)
if probe.returncode:
    raise SystemExit("STOP: Corrected graph not visible in container")

source = backend.read_text()
ast.parse(source)
lines = source.splitlines()

old_graph = "/batch2/cta_max/grecbase_fusion_batch2_draft.py"
old_dir = "/batch2/cta_max"

# Change only the graph loader's path literal.
tokens = []
changes = []

for token in tokenize.generate_tokens(io.StringIO(source).readline):
    if token.type == tokenize.STRING:
        try:
            value = ast.literal_eval(token.string)
        except (ValueError, SyntaxError):
            value = None

        graph_nearby = any(
            "grecbase_fusion_batch2_draft.py" in lines[j]
            for j in range(
                max(0, token.start[0] - 5),
                min(len(lines), token.start[0] + 4)
            )
        )

        if value == old_graph:
            token = token._replace(string=repr(str(graph)))
            changes.append("FULL GRAPH PATH")

        elif (
            value == old_dir
            and token.start[0] > 75
            and graph_nearby
        ):
            token = token._replace(string=repr(str(candidate)))
            changes.append("GRAPH DIRECTORY")

    tokens.append(token)

if len(changes) != 1:
    print("GRAPH LOADER SOURCE:")
    for i in range(82, min(105, len(lines))):
        print(f"{i+1}: {lines[i]}")
    raise SystemExit(
        f"STOP: Expected one graph-path correction; found {len(changes)}"
    )

updated = tokenize.untokenize(tokens)
ast.parse(updated)

backup = dev / "real_max_batch2_backend.py.before_graph_loader_fix"

if backup.exists():
    raise SystemExit("STOP: Backup already exists")

if shutil.disk_usage(dev).free < 20 * 1024 * 1024:
    raise SystemExit("STOP: Insufficient disk space")

shutil.copy2(backend, backup)

fd, temporary = tempfile.mkstemp(
    prefix=".batch2_graph_fix_",
    dir=str(dev)
)
try:
    with os.fdopen(fd, "w") as f:
        f.write(updated)
    os.chmod(temporary, backend.stat().st_mode)
    os.replace(temporary, backend)
finally:
    if os.path.exists(temporary):
        os.unlink(temporary)

print("GRAPH LOADER PATH: CORRECTED")
print("HOST SYNTAX: PASS")

smoke = """
import importlib.util
from pathlib import Path

p = Path("/batch2/real_max_batch2_backend.py")
spec = importlib.util.spec_from_file_location(
    "cta_batch2_final_import_check", p
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

assert callable(module.infer_max_batch)
print("BATCH-2 BACKEND IMPORT: PASS", flush=True)
"""

r = container_run(smoke)
print(r.stdout)
if r.stderr:
    print(r.stderr[-2500:])

print("IMPORT EXIT CODE:", r.returncode)
print("ORIGINAL DS/MAX: UNCHANGED")
print("CONTAINERS RESTARTED: NONE")
PY
