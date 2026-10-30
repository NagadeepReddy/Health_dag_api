python3 -B - <<'PY'
from pathlib import Path
import ast, json, os, shutil, subprocess

root = Path("/application1")
repo = root / "sajjna8/rt-pzaas-cta-offers-v1"
dev = root / "CTA_MAX_TRUE_BATCH2_DEV_20261029"
cand = root / "cta_max_true_batch_dev_20261028/batch2_candidate/cta_max"

graph = cand / "grecbase_fusion_full_head_72_max.py"
backend = dev / "real_max_batch2_backend.py"
original = repo / "artifacts/v1.168-max/cta_max/grecbase_aux_branches_max.py"
existing = cand / "grecbase_aux_branches_max.py"
target = cand / "grecbase_aux_branches_batch2_verified.py"

source = existing if existing.is_file() else original

for p in (graph, backend, source):
    if not p.is_file() or p.is_symlink():
        raise SystemExit("STOP: Required source unavailable: " + str(p))

# Correct only batch-leading dimensions in the isolated auxiliary helper.
tree = ast.parse(source.read_text())

class BatchAuxFix(ast.NodeTransformer):
    def __init__(self):
        self.inside = False
        self.fixed = 0
        self.already = 0

    def visit_FunctionDef(self, node):
        previous = self.inside
        if node.name == "grecbase_aux_features":
            self.inside = True
        self.generic_visit(node)
        self.inside = previous
        return node

    def visit_Call(self, node):
        self.generic_visit(node)
        if not self.inside:
            return node

        if not (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "reshape"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "ops"
            and len(node.args) >= 2
        ):
            return node

        shape = node.args[1]
        if not isinstance(shape, (ast.List, ast.Tuple)):
            return node

        if len(shape.elts) != 2:
            return node

        try:
            dims = [ast.literal_eval(x) for x in shape.elts]
        except (ValueError, TypeError, SyntaxError):
            return node

        if dims == [1, 256]:
            shape.elts[0] = ast.Constant(value=2)
            self.fixed += 1
        elif dims == [2, 256]:
            self.already += 1

        return node

fix = BatchAuxFix()
tree = fix.visit(tree)
ast.fix_missing_locations(tree)

if fix.fixed + fix.already == 0:
    raise SystemExit("STOP: Expected auxiliary reshape not identified")

helper_code = ast.unparse(tree) + "\n"
ast.parse(helper_code)

print("AUXILIARY RESHAPES CORRECTED:", fix.fixed)
print("ALREADY BATCH-COMPATIBLE:", fix.already)

# Redirect only the isolated graph's auxiliary import.
graph_source = graph.read_text()
graph_tree = ast.parse(graph_source)

matches = [
    n for n in ast.walk(graph_tree)
    if isinstance(n, ast.ImportFrom)
    and any(a.name == "grecbase_aux_features" for a in n.names)
]

if len(matches) != 1:
    raise SystemExit("STOP: Unexpected auxiliary import count")

node = matches[0]
old_module = "cta_max.grecbase_aux_branches_max"
new_module = "cta_max.grecbase_aux_branches_batch2_verified"

if node.module not in (old_module, new_module):
    raise SystemExit("STOP: Unexpected auxiliary module")

if node.end_lineno != node.lineno:
    raise SystemExit("STOP: Multiline import requires manual review")

lines = graph_source.splitlines(keepends=True)

if node.module == old_module:
    line = lines[node.lineno - 1]
    if line.count(old_module) != 1:
        raise SystemExit("STOP: Unexpected import statement")
    lines[node.lineno - 1] = line.replace(old_module, new_module, 1)

updated_graph = "".join(lines)
ast.parse(updated_graph)

# Confirm adequate disk space and existing container.
if shutil.disk_usage(cand).free < 20 * 1024 * 1024:
    raise SystemExit("STOP: Low disk space")

P = [
    "podman",
    "--root", "/application1/podman/storage",
    "--runroot", "/run/containers/storage"
]

ids = []

for cid in subprocess.check_output(P + ["ps", "-q"], text=True).split():
    info = json.loads(
        subprocess.check_output(P + ["inspect", cid], text=True)
    )[0]

    if any(
        m.get("Source") == str(dev)
        and m.get("Destination") == "/batch2"
        for m in info.get("Mounts", [])
    ):
        ids.append(cid)

if len(ids) != 1:
    raise SystemExit("STOP: Existing Batch-2 container unavailable")

# Stage new helper without overwriting previous corrections.
if target.exists():
    if target.is_symlink() or target.read_text() != helper_code:
        raise SystemExit("STOP: Existing verified helper differs")
else:
    with target.open("x") as f:
        f.write(helper_code)
    print("ISOLATED AUXILIARY HELPER: INSTALLED")

if updated_graph != graph_source:
    backup = graph.with_name(graph.name + ".before_aux_batch2_fix")
    temp = graph.with_name(".aux_batch2_graph.tmp")

    if backup.exists() or temp.exists():
        raise SystemExit("STOP: Backup/temp conflict")

    shutil.copy2(graph, backup)

    try:
        with temp.open("x") as f:
            f.write(updated_graph)
        os.chmod(temp, graph.stat().st_mode)
        os.replace(temp, graph)
    finally:
        if temp.exists():
            temp.unlink()

print("ISOLATED GRAPH IMPORT: CORRECTED")
print("PYTHON SYNTAX: PASS")

# Build the COMPLETE graph without running trained inference.
code = r'''
import importlib.util, inspect
from pathlib import Path
from max.graph import DeviceRef

p = Path("/batch2/real_max_batch2_backend.py")
spec = importlib.util.spec_from_file_location("batch2_graph_check", p)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

helper = mod._cta_module.grecbase_aux_features
actual = Path(inspect.getsourcefile(helper)).resolve()

expected = Path(
    "/application1/cta_max_true_batch_dev_20261028/"
    "batch2_candidate/cta_max/"
    "grecbase_aux_branches_batch2_verified.py"
).resolve()

assert actual == expected, (
    "Wrong auxiliary source: " + str(actual)
)

print("CORRECTED AUXILIARY IMPORT: PASS", flush=True)
print("BUILDING COMPLETE BATCH-2 GRAPH...", flush=True)

graph = mod.build_grecbase_fusion_graph_order_correct(
    DeviceRef.CPU()
)

assert len(graph.inputs) == 72

print("COMPLETE BATCH-2 GRAPH BUILD: PASS", flush=True)
print("GRAPH INPUTS:", len(graph.inputs), flush=True)
'''

try:
    r = subprocess.run(
        P + [
            "exec", "-i", "-w", "/workspace",
            "-e", "PYTHONDONTWRITEBYTECODE=1",
            "-e", "TMPDIR=/tmp",
            "-e", "PYTHONPATH=/batch2:/workspace/artifacts/v1.168-max",
            ids[0], "/opt/venv/bin/python", "-B", "-"
        ],
        input=code,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=120
    )

    print(r.stdout[-5000:])
    print("GRAPH BUILD EXIT CODE:", r.returncode)

except subprocess.TimeoutExpired:
    print("STOP: Graph construction exceeded 120 seconds")

print("ORIGINAL DS/MAX: UNCHANGED")
print("CONTAINERS RESTARTED: NONE")
PY
