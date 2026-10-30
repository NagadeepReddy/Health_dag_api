python3 -B <<'PY'
import json, subprocess, shutil, socket, time, re
from pathlib import Path

POD = ["podman", "--root", "/application1/podman/storage",
       "--runroot", "/run/containers/storage"]
OLD = "cta-batch2-importfirst-8766-10g"
NEW = "cta-batch2-contractfix-8766-10g"
ROOT = Path("/application1/cta_max_true_batch_dev_20261028/batch2_candidate")
FIXTURE = "/workspace/artifacts/v1.168-max/cta_native_adjusted_sanity_input.json"

def cmd(args, data=None, timeout=90):
    return subprocess.run(args, input=data, text=True,
                          capture_output=True, timeout=timeout)

def stop(msg):
    raise SystemExit("STOP: " + msg)

def inspect(name):
    r = cmd(POD + ["inspect", name])
    if r.returncode:
        stop("Cannot inspect " + name + ": " + r.stderr[-600:])
    return json.loads(r.stdout)[0]

print("=== FINAL BATCH-2 CONTROLLED RECOVERY ===", flush=True)

old = inspect(OLD)
mounts = [m for m in old["Mounts"] if m["Destination"] == "/batch2"]

if len(mounts) != 1 or Path(mounts[0]["Source"]).resolve() != ROOT.resolve():
    stop("Verified Batch-2 mount differs")

if old["HostConfig"]["Memory"] != 10737418240:
    stop("Expected 10 GiB memory limit missing")

graph = ROOT / "cta_max/grecbase_fusion_batch2_draft.py"
helper = ROOT / "cta_max/grecbase_aux_features_max.py"

if not graph.is_file() or not helper.is_file():
    stop("Active Batch-2 files missing")

if not re.search(r"return\s+task\s*,\s*ihq\s*,\s*jet\b", helper.read_text()):
    stop("Previously patched helper contract not present")

if not re.search(r"task\s*,\s*ihq\s*,\s*jet\s*=\s*grecbase_aux_features\s*\(", graph.read_text()):
    stop("Three-output caller not confirmed")

if shutil.disk_usage("/application1").free < 15 * 1024**3:
    stop("Less than 15 GiB application storage free")

mem = next(int(x.split()[1]) for x in
           Path("/proc/meminfo").read_text().splitlines()
           if x.startswith("MemAvailable:"))

if mem < 12 * 1024**2:
    stop("Less than 12 GiB host available memory")

print("GRAPH + CONTRACT: PASS")
print("DISK + MEMORY: PASS", flush=True)

name = OLD
state = old["State"]["Status"]

if state == "running":
    print("OLD CONTAINER RUNNING; REUSING IT")
else:
    try:
        with socket.create_connection(("127.0.0.1", 8766), 1):
            stop("Port 8766 already occupied")
    except (ConnectionRefusedError, TimeoutError, OSError):
        pass

    r = cmd(POD + ["container", "exists", NEW])
    if r.returncode == 0:
        stop("Recovery clone already exists; no duplicate")

    print("CREATING FRESH ISOLATED CLONE", flush=True)
    r = cmd(POD + ["container", "clone", "--name=" + NEW, OLD], timeout=100)
    if r.returncode:
        stop("Clone failed: " + r.stderr[-1400:])

    new = inspect(NEW)
    if new["HostConfig"]["Memory"] != 10737418240:
        stop("Clone memory configuration differs")

    if not any(m["Destination"] == "/batch2"
               and Path(m["Source"]).resolve() == ROOT.resolve()
               for m in new["Mounts"]):
        stop("Clone mount configuration differs")

    r = cmd(POD + ["start", NEW], timeout=100)
    if r.returncode:
        stop("Fresh container start failed: " + r.stderr[-1500:])

    name = NEW
    print("FRESH CONTAINER STARTED:", name, flush=True)

health = '''
import urllib.request
with urllib.request.urlopen(
 "http://127.0.0.1:8766/health", timeout=3
) as r:
 assert r.status == 200
'''

healthy = False
for i in range(50):
    state = inspect(name)["State"]
    if state["Status"] != "running" or state.get("OOMKilled"):
        break
    r = cmd(POD + ["exec", name, "/opt/venv/bin/python",
                   "-B", "-c", health], timeout=12)
    if r.returncode == 0:
        healthy = True
        break
    time.sleep(3)

if not healthy:
    r = cmd(POD + ["logs", "--tail", "65", name])
    print((r.stdout + r.stderr)[-4500:])
    stop("Native server failed health check")

print("NATIVE HEALTH: PASS", flush=True)

test = r'''
import json, urllib.request, urllib.error
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

fixture = Path("/workspace/artifacts/v1.168-max/cta_native_adjusted_sanity_input.json")
assert fixture.is_file(), "Verified real CTA fixture missing"

payload = json.loads(fixture.read_text())
body = json.dumps(payload).encode()
url = "http://127.0.0.1:8766/v2/cta/predict"

def send(n):
    request = urllib.request.Request(
        url, data=body, method="POST",
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=110) as r:
            status = r.status
            result = json.loads(r.read())
    except urllib.error.HTTPError as e:
        return n, e.code, False, e.read().decode(errors="replace")[:1000]
    except Exception as e:
        return n, 0, False, str(e)

    offers = result.get("jsonData", {}).get(
        "prediction", {}).get("offerList")
    return n, status, isinstance(offers, list), str(result)[:500]

with ThreadPoolExecutor(max_workers=2) as pool:
    results = list(pool.map(send, (1, 2)))

for n, status, valid, detail in results:
    print(f"REQUEST {n}: HTTP {status}, VALID_CTA={valid}")
    if status != 200 or not valid:
        print("ERROR:", detail)

print("REAL NATIVE HTTP 2/2:",
      "PASS" if all(s == 200 and v for _, s, v, _ in results)
      else "FAIL")
'''

print("\n=== REAL NATIVE BATCH-2 REQUESTS ===", flush=True)
r = cmd(POD + ["exec", "-i", name,
               "/opt/venv/bin/python", "-B", "-"],
        data=test, timeout=240)

print(r.stdout)
if r.returncode:
    print(r.stderr[-1800:])

print("\n=== EXECUTION EVIDENCE ===")
r = cmd(POD + ["logs", "--tail", "350", name])
lines = (r.stdout + r.stderr).splitlines()

for line in lines:
    if re.search(
        r"BATCH.?2|batch.size|ENGINE_ID|EXECUT|Worker failed|Traceback|OOM",
        line, re.I
    ):
        print(line[:420])

print("\n=== FINAL ===")
print("CONTAINER:", name)
print("STATE:", inspect(name)["State"]["Status"])
print("ORIGINAL DS/MAX: UNCHANGED")
print("OLD CONTAINER: PRESERVED")
print("COALESCING: NEEDS ONE-BATCH EXECUTION PROOF")
PY
