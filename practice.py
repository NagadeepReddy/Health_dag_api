python3 -B <<'PY'
import ast, json, re, shutil, subprocess, time, os
from pathlib import Path

POD = ["podman", "--root", "/application1/podman/storage",
       "--runroot", "/run/containers/storage"]
NAME = "cta-batch2-importfirst-8766-10g"
EXPECTED = Path("/application1/cta_max_true_batch_dev_20261028/batch2_candidate").resolve()

def run(args, input=None, timeout=90):
    return subprocess.run(args, input=input, text=True,
                          capture_output=True, timeout=timeout)

def stop(message):
    raise SystemExit("STOP: " + message)

print("=== ISOLATED BATCH-2 CONTRACT REPAIR ===", flush=True)

r = run(POD + ["inspect", NAME])
if r.returncode:
    stop(r.stderr)

info = json.loads(r.stdout)[0]
state = info["State"]
if state["Status"] != "running" or state.get("OOMKilled"):
    stop("Container not healthy for restart")

if int(info["HostConfig"]["Memory"]) != 10737418240:
    stop("Expected 10 GiB memory limit missing")

mounts = [m for m in info["Mounts"]
          if m["Destination"] == "/batch2"]
if len(mounts) != 1:
    stop("Unique /batch2 mount missing")

root = Path(mounts[0]["Source"]).resolve()
if root != EXPECTED:
    stop("Unexpected mounted source: " + str(root))

graph = root / "cta_max/grecbase_fusion_batch2_draft.py"
if not graph.is_file():
    stop("Active graph missing")

source = graph.read_text()
tree = ast.parse(source)

if not re.search(
    r"task\s*,\s*ihq\s*,\s*jet\s*=\s*grecbase_aux_features\s*\(",
    source
):
    stop("Expected three-value caller missing")

modules = set()
for node in ast.walk(tree):
    if isinstance(node, ast.ImportFrom):
        if any(a.name == "grecbase_aux_features"
               for a in node.names):
            modules.add(node.module)

if len(modules) != 1:
    stop("Helper import requires review: " + str(modules))

module = next(iter(modules))
if not module.startswith("cta_max."):
    stop("Helper is not isolated CTA MAX")

helper = root / (module.replace(".", "/") + ".py")
if not helper.is_file():
    stop("Imported helper missing: " + str(helper))

old = helper.read_text()

pattern = re.compile(
    r"(?m)^(?P<indent>[ \t]*)return[ \t]+ops\.concat"
    r"\(\[[ \t]*task[ \t]*,[ \t]*ihq[ \t]*,"
    r"[ \t]*jet[ \t]*\][ \t]*,[ \t]*axis[ \t]*="
    r"[ \t]*1[ \t]*\)[ \t]*$"
)

matches = list(pattern.finditer(old))
if len(matches) != 1:
    stop("Expected single TensorValue return not found; no changes")

new = pattern.sub(
    lambda m: m.group("indent") + "return task, ihq, jet",
    old
)

compile(new, str(helper), "exec")

backup = helper.with_name(helper.name + ".before_tuple_fix.bak")
if backup.exists():
    stop("Backup already exists; refusing overwrite")

shutil.copy2(helper, backup)
temp = helper.with_name(helper.name + ".tuple_fix_tmp")

try:
    temp.write_text(new)
    shutil.copymode(helper, temp)
    os.replace(temp, helper)
finally:
    if temp.exists():
        temp.unlink()

print("HELPER:", helper)
print("BACKUP:", backup)
print("RETURN CONTRACT: CORRECTED")
print("SYNTAX: PASS")
print("ORIGINAL DS/MAX: UNCHANGED", flush=True)

print("\n=== RESTART ISOLATED CONTAINER ONLY ===", flush=True)
r = run(POD + ["restart", "-t", "15", NAME], timeout=100)
if r.returncode:
    stop("Isolated restart failed: " + r.stderr)

print("ISOLATED RESTART: COMPLETE", flush=True)

health_code = """
import urllib.request
with urllib.request.urlopen(
    "http://127.0.0.1:8766/health", timeout=3
) as r:
    assert r.status == 200
"""

healthy = False
for i in range(40):
    r = run(POD + [
        "exec", NAME, "/opt/venv/bin/python",
        "-B", "-c", health_code
    ], timeout=12)
    if r.returncode == 0:
        healthy = True
        break
    time.sleep(3)

if not healthy:
    r = run(POD + ["logs", "--tail", "65", NAME])
    print(r.stdout[-5000:])
    stop("Native MAX health did not recover")

print("NATIVE MAX HEALTH: PASS", flush=True)

print("\n=== TWO REAL CTA HTTP REQUESTS ===", flush=True)

test_code = r'''
import json, urllib.request, urllib.error
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

fixture = Path(
    "/workspace/artifacts/v1.168-max/"
    "cta_native_adjusted_sanity_input.json"
)
assert fixture.is_file(), "Real CTA fixture missing"
payload = json.loads(fixture.read_text())
body = json.dumps(payload).encode()

url = "http://127.0.0.1:8766/v2/cta/predict"

def request(n):
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            status = r.status
            result = json.loads(r.read())
    except urllib.error.HTTPError as e:
        status = e.code
        result = {"error": e.read().decode(errors="replace")[:1800]}
    except Exception as e:
        return n, 0, False, str(e)

    offers = (
        result.get("jsonData", {})
              .get("prediction", {})
              .get("offerList")
    )
    return n, status, isinstance(offers, list), str(result)[:700]

with ThreadPoolExecutor(max_workers=2) as pool:
    results = list(pool.map(request, [1, 2]))

for n, status, valid, detail in results:
    print(f"REQUEST {n}: HTTP {status} VALID_CTA={valid}")
    if status != 200 or not valid:
        print("DETAIL:", detail)

passed = all(s == 200 and valid
             for _, s, valid, _ in results)

print("REAL HTTP 2/2:", "PASS" if passed else "FAIL")
assert passed, "Native CTA requests still failing"
'''

r = run(
    POD + ["exec", "-i", "-e", "PYTHONDONTWRITEBYTECODE=1",
           NAME, "/opt/venv/bin/python", "-B", "-"],
    input=test_code,
    timeout=200
)

print(r.stdout)
if r.returncode:
    print(r.stderr[-2500:])
    print("HTTP VALIDATION: NOT PASSED")
else:
    print("HTTP VALIDATION: PASSED")

print("\n=== RECENT BATCH EXECUTION EVIDENCE ===")
r = run(POD + ["logs", "--tail", "220", NAME])
for line in (r.stdout + r.stderr).splitlines():
    if re.search(
        r"BATCH|ENGINE_ID|EXECUT|reshape|TensorValue|Worker failed",
        line, re.I
    ):
        print(line[:450])

print("\nORIGINAL DS/MAX: UNCHANGED")
print("SINGLE MAX BATCH EXECUTION: REQUIRES LOG CONFIRMATION")
PY
