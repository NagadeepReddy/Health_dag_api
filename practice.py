python3 -B - <<'PY'
from pathlib import Path
import ast, json, os, shutil, subprocess, tempfile

root = Path("/application1")
dev = root / "CTA_MAX_TRUE_BATCH2_DEV_20261029"
cand = root / "cta_max_true_batch_dev_20261028/batch2_candidate/cta_max"
graph = cand / "grecbase_fusion_full_head_72_max.py"
alias = cand / "grecbase_aux_branches_batch2_verified.py"

P = ["podman", "--root", "/application1/podman/storage",
     "--runroot", "/run/containers/storage"]

if not graph.is_file() or graph.is_symlink():
    raise SystemExit("STOP: Isolated graph unavailable")

# Find the already-corrected auxiliary implementation.
def shapes_and_function(path):
    tree = ast.parse(path.read_text())
    names = {
        n.name for n in tree.body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    shapes = set()
    for n in ast.walk(tree):
        if not (
            isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute)
            and n.func.attr == "reshape"
            and len(n.args) >= 2
            and isinstance(n.args[1], (ast.List, ast.Tuple))
        ):
            continue
        try:
            dims = tuple(ast.literal_eval(x) for x in n.args[1].elts)
            shapes.add(dims)
        except (ValueError, TypeError, SyntaxError):
            pass
    return names, shapes

locations = [
    cand / "grecbase_aux_branches_max.py",
    dev / "grecbase_aux_branches_max.py",
    dev / "cta_max/grecbase_aux_branches_max.py",
]

locations += sorted(cand.glob("*aux*batch*.py"))
locations += sorted(dev.glob("*aux*batch*.py"))

selected = None
for p in dict.fromkeys(locations):
    if not p.is_file() or p.is_symlink() or p == alias:
        continue
    names, shapes = shapes_and_function(p)
    if (
        "grecbase_aux_features" in names
        and (2, 256) in shapes
        and (2, 1, 128) in shapes
    ):
        selected = p
        break

if selected is None:
    raise SystemExit(
        "STOP: Previously corrected auxiliary implementation "
        "not located in known development paths. No files changed."
    )

print("REUSING CORRECTED AUXILIARY:", selected, flush=True)

# Verify the existing graph import before editing.
source = graph.read_text()
tree = ast.parse(source)
imports = [
    n for n in ast.walk(tree)
    if isinstance(n, ast.ImportFrom)
    and any(a.name == "grecbase_aux_features" for a in n.names)
]

if len(imports) != 1:
    raise SystemExit("STOP: Auxiliary import is not unique")

node = imports[0]
old_module = "cta_max.grecbase_aux_branches_max"
new_module = "cta_max.grecbase_aux_branches_batch2_verified"

if node.module not in (old_module, new_module):
    raise SystemExit("STOP: Unexpected auxiliary import")

if node.end_lineno != node.lineno:
    raise SystemExit("STOP: Unexpected multiline import")

lines = source.splitlines(keepends=True)

if node.module == old_module:
    i = node.lineno - 1
    if lines[i].count(old_module) != 1:
        raise SystemExit("STOP: Import statement differs")
    lines[i] = lines[i].replace(old_module, new_module, 1)

updated = "".join(lines)
ast.parse(updated)

if alias.exists():
    if alias.is_symlink() or alias.read_bytes() != selected.read_bytes():
        raise SystemExit("STOP: Existing alias differs")

# Reuse the already-running Batch-2 container.
matches = []
for cid in subprocess.check_output(P + ["ps", "-q"], text=True).split():
    info = json.loads(subprocess.check_output(
        P + ["inspect", cid], text=True))[0]
    if any(
        m.get("Source") == str(dev)
        and m.get("Destination") == "/batch2"
        for m in info.get("Mounts", [])
    ):
        matches.append(cid)

if len(matches) != 1:
    raise SystemExit("STOP: Existing development container unavailable")

available = int(next(
    line.split()[1]
    for line in Path("/proc/meminfo").read_text().splitlines()
    if line.startswith("MemAvailable:")
)) // 1024

print("AVAILABLE RAM MB:", available)

if available < 10000 or shutil.disk_usage(cand).free < 20*1024*1024:
    raise SystemExit("STOP: Resource safety gate failed")

backup = graph.with_name(graph.name + ".before_verified_aux_reuse")
changed = updated != source
created_alias = False

if changed and backup.exists():
    raise SystemExit("STOP: Backup conflict")

# Stage only isolated development changes.
if not alias.exists():
    shutil.copy2(selected, alias)
    created_alias = True

if changed:
    shutil.copy2(graph, backup)
    fd, temp = tempfile.mkstemp(prefix=".aux_batch2_", dir=str(cand))
    try:
        with os.fdopen(fd, "w") as f:
            f.write(updated)
        os.chmod(temp, graph.stat().st_mode)
        os.replace(temp, graph)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)

print("CORRECTED AUXILIARY IMPORT: STAGED", flush=True)

# Validate actual imported helper and complete graph.
code = '''
import importlib.util, inspect
from pathlib import Path
from max.graph import DeviceRef

p = Path("/batch2/real_max_batch2_backend.py")
spec = importlib.util.spec_from_file_location("cta_batch2_check", p)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

actual = Path(
    inspect.getsourcefile(mod._cta_module.grecbase_aux_features)
).resolve()

expected = Path(
    "/application1/cta_max_true_batch_dev_20261028/"
    "batch2_candidate/cta_max/"
    "grecbase_aux_branches_batch2_verified.py"
).resolve()

print("ACTIVE AUXILIARY:", actual, flush=True)
assert actual == expected

print("BUILDING COMPLETE BATCH-2 GRAPH...", flush=True)

g = mod.build_grecbase_fusion_graph_order_correct(
    DeviceRef.CPU()
)

assert len(g.inputs) == 72
print("COMPLETE BATCH-2 GRAPH: PASS", flush=True)
print("GRAPH INPUTS: 72", flush=True)
'''

try:
    r = subprocess.run(
        P + [
            "exec", "-i", "-w", "/workspace",
            "-e", "PYTHONDONTWRITEBYTECODE=1",
            "-e", "TMPDIR=/tmp",
            "-e", "PYTHONPATH=/batch2:/workspace/artifacts/v1.168-max",
            matches[0], "/opt/venv/bin/python", "-B", "-"
        ],
        input=code, text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=120
    )
    print(r.stdout[-4500:])
    passed = r.returncode == 0
except subprocess.TimeoutExpired as e:
    out = e.stdout or b""
    if isinstance(out, bytes):
        out = out.decode(errors="replace")
    print(out[-2500:])
    passed = False

if not passed:
    if changed:
        shutil.copy2(backup, graph)
    if created_alias:
        alias.unlink()
    print("GRAPH CHECK FAILED — ISOLATED CHANGE ROLLED BACK")
else:
    print("CORRECTED AUXILIARY + COMPLETE GRAPH: PASS")

print("ORIGINAL DS/MAX: UNCHANGED")
print("CONTAINERS RESTARTED: NONE")
PY
