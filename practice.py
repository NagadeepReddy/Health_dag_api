python3 -B <<'PY'
import ast, json, os, shutil, subprocess, time
from pathlib import Path

POD = ["podman", "--root", "/application1/podman/storage",
       "--runroot", "/run/containers/storage"]
NAME = "cta-batch2-importfirst-8766-10g"

def run(args, data=None, timeout=120):
    return subprocess.run(args, input=data, text=True,
                          capture_output=True, timeout=timeout)

def stop(reason):
    raise SystemExit("STOP: " + reason)

print("=== ACTIVE BATCH-2 DIRECT HELPER REPAIR ===", flush=True)

r = run(POD + ["inspect", NAME])
if r.returncode:
    stop(r.stderr)

info = json.loads(r.stdout)[0]

if info["State"]["Status"] != "running":
    stop("Isolated container not running")

if int(info["HostConfig"]["Memory"]) != 10737418240:
    stop("10 GiB limit not confirmed")

mounts = [m for m in info["Mounts"]
          if m["Destination"] == "/batch2"]

if len(mounts) != 1:
    stop("Active Batch-2 mount missing")

root = Path(mounts[0]["Source"]).resolve()

expected = Path(
    "/application1/cta_max_true_batch_dev_20261028/"
    "batch2_candidate"
).resolve()

if root != expected:
    stop("Unexpected source: " + str(root))

graph = root / "cta_max/grecbase_fusion_batch2_draft.py"
helper = root / "cta_max/grecbase_aux_features_max.py"

if not graph.is_file() or not helper.is_file():
    stop("Known Batch-2 files missing")

gtext = graph.read_text()

if "grecbase_aux_features_max.py" not in gtext:
    stop("Active graph does not reference expected helper")

if "task, ihq, jet = grecbase_aux_features(" not in gtext:
    stop("Expected three-output caller not confirmed")

source = helper.read_text()
tree = ast.parse(source)

functions = [
    n for n in tree.body
    if isinstance(n, ast.FunctionDef)
    and n.name == "grecbase_aux_features"
]

if len(functions) != 1:
    stop("Expected helper function not unique")

class Returns(ast.NodeVisitor):
    def __init__(self):
        self.items = []
    def visit_FunctionDef(self, node):
        pass
    def visit_AsyncFunctionDef(self, node):
        pass
    def visit_Return(self, node):
        self.items.append(node)

finder = Returns()
for node in functions[0].body:
    finder.visit(node)

if len(finder.items) != 1:
    stop("Helper return contract requires review")

ret = finder.items[0]
value = ret.value

print("ACTIVE HELPER:", helper)
print("ACTUAL RETURN:", ast.get_source_segment(source, ret))
print("EXPECTED: THREE SEPARATE TENSORS", flush=True)

if isinstance(value, ast.Tuple):
    stop("Helper already returns a tuple; no patch justified")

valid = (
    isinstance(value, ast.Call)
    and isinstance(value.func, ast.Attribute)
    and isinstance(value.func.value, ast.Name)
    and value.func.value.id == "ops"
    and value.func.attr == "concat"
    and len(value.args) >= 1
    and isinstance(value.args[0], (ast.List, ast.Tuple))
    and [x.id for x in value.args[0].elts
         if isinstance(x, ast.Name)] == ["task", "ihq", "jet"]
    and len(value.args[0].elts) == 3
)

if not valid:
    stop("Return is not the confirmed three-tensor concat")

if shutil.disk_usage(root).free < 2 * 1024**3:
    stop("Insufficient safe disk space")

fixture = (
    "/workspace/artifacts/v1.168-max/"
    "cta_native_adjusted_sanity_input.json"
)

r = run(POD + ["exec", NAME, "test", "-f", fixture])
if r.returncode:
    stop("Real CTA fixture not available in container")

lines = source.splitlines(keepends=True)
start = sum(len(x) for x in lines[:ret.lineno-1]) + ret.col_offset
end = sum(len(x) for x in lines[:ret.end_lineno-1]) + ret.end_col_offset

updated = (
    source[:start] +
    "return task, ihq, jet" +
    source[end:]
)

compile(updated, str(helper), "exec")

backup = helper.with_name(helper.name + ".before_contract_fix.bak")
if backup.exists():
    stop("Backup already exists; refusing overwrite")

shutil.copy2(helper, backup)
tmp = helper.with_name(helper.name + ".contract_fix_tmp")

try:
    tmp.write_text(updated)
    shutil.copymode(helper, tmp)
    os.replace(tmp, helper)
finally:
    if tmp.exists():
        tmp.unlink()

print("\nBACKUP: PRESERVED")
print("ISOLATED RETURN CONTRACT: PATCHED")
print("SYNTAX: PASS")
print("ORIGINAL DS/MAX: UNCHANGED", flush=True)

print("\n=== ISOLATED RESTART ===", flush=True)

r = run(POD + ["restart", "-t", "15", NAME], timeout=90)
if r.returncode:
    stop("Restart failed: " + r.stderr)

health = '''
import urllib.request
with urllib.request.urlopen(
    "http://127.0.0.1:8766/health", timeout=3
) as r:
    assert r.status == 200
'''

healthy = False
for i in range(40):
    r = run(POD + [
        "exec", NAME, "/opt/venv/bin/python",
        "-B", "-c", health
    ], timeout=12)

    if r.returncode == 0:
        healthy = True
        break

    time.sleep(3)

if not healthy:
    r = run(POD + ["logs", "--tail", "70", NAME])
    print(r.stdout[-5000:])
    stop("Native MAX health failed")

print("NATIVE HEALTH: PASS", flush=True)

test = '''
import json, urllib.request, urllib.error
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

p = Path("/workspace/artifacts/v1.168-max/"
         "cta_native_adjusted_sanity_input.json")
data = json.dumps(json.loads(p.read_text())).encode()

def send(n):
    req = urllib.request.Request(
        "http://127.0.0.1:8766/v2/cta/predict",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            status = r.status
            result = json.loads(r.read())
    except urllib.error.HTTPError as e:
        status = e.code
        result = {"error": e.read().decode(errors="replace")[:1000]}
    except Exception as e:
        return n, 0, False, str(e)

    valid = isinstance(result, dict) and bool(result.get("jsonData"))
    return n, status, valid, str(result)[:600]

with ThreadPoolExecutor(max_workers=2) as pool:
    results = list(pool.map(send, [1, 2]))

for n, status, valid, detail in results:
    print(f"REQUEST {n}: HTTP {status} CTA_JSON={valid}")
    if status != 200 or not valid:
        print("DETAIL:", detail)

passed = all(s == 200 and valid
             for _, s, valid, _ in results)

print("HTTP 2/2:", "PASS" if passed else "FAIL")
'''

r = run(
    POD + ["exec", "-i", NAME,
           "/opt/venv/bin/python", "-B", "-"],
    data=test,
    timeout=210
)

print(r.stdout)
if r.returncode:
    print(r.stderr[-2000:])
    print("HTTP RESULT: NOT VERIFIED")

print("\n=== RECENT NATIVE MAX EVIDENCE ===")
r = run(POD + ["logs", "--tail", "160", NAME])

for line in (r.stdout + r.stderr).splitlines():
    if any(x in line.lower() for x in [
        "batch", "engine_id", "execut",
        "tensorvalue", "worker failed", "traceback"
    ]):
        print(line[:350])

print("\nORIGINAL DS/MAX: UNCHANGED")
print("BATCH COALESCING: REQUIRES EXECUTION EVIDENCE")
PY
