python3 -B <<'PY'
import subprocess, json, os, re, time, shutil, socket
from pathlib import Path
from datetime import datetime, timezone

POD = ["podman", "--root", "/application1/podman/storage",
       "--runroot", "/run/containers/storage"]
NAME = "cta-batch2-importfirst-8766-10g"
BASE = Path("/application1/cta_max_true_batch_dev_20261028/batch2_candidate")
HELPER = BASE / "cta_max/grecbase_aux_features_max.py"

def run(args, data=None, timeout=90):
    return subprocess.run(args, input=data, text=True,
                          capture_output=True, timeout=timeout)

def stop(msg):
    raise SystemExit("STOP: " + str(msg))

def inspect():
    r = run(POD + ["inspect", NAME])
    if r.returncode:
        stop(r.stderr[-1000:])
    return json.loads(r.stdout)[0]

print("=== EXISTING ISOLATED CONTAINER RECOVERY ===", flush=True)

c = inspect()
state = c["State"]["Status"]

print("CURRENT STATE:", state)

if state not in ("running", "exited", "created", "configured"):
    stop("Unexpected container state")

if int(c["HostConfig"]["Memory"]) != 10737418240:
    stop("Expected 10 GiB memory configuration missing")

mounts = [m for m in c["Mounts"] if m["Destination"] == "/batch2"]
if len(mounts) != 1 or Path(mounts[0]["Source"]).resolve() != BASE.resolve():
    stop("Active Batch-2 mount mismatch")

if not HELPER.is_file():
    stop("Known isolated helper missing")

if not re.search(r"return\s+task\s*,\s*ihq\s*,\s*jet\b",
                 HELPER.read_text()):
    stop("Previously patched helper contract missing")

if shutil.disk_usage("/application1").free < 15 * 1024**3:
    stop("Insufficient application1 disk capacity")

meminfo = Path("/proc/meminfo").read_text()
available = int(re.search(r"MemAvailable:\s+(\d+)", meminfo).group(1)) * 1024

if available < 12 * 1024**3:
    stop("Insufficient available host memory")

print("10 GiB LIMIT: VERIFIED")
print("RETURN CONTRACT: VERIFIED")
print("HOST SAFETY: PASS", flush=True)

since = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

if state != "running":
    try:
        with socket.create_connection(("127.0.0.1", 8766), timeout=2):
            stop("Port 8766 occupied by another process")
    except OSError:
        pass

    print("\n=== RESTORE PODMAN ROOTFS MOUNT ===", flush=True)

    r = run(POD + ["mount", NAME], timeout=60)
    if r.returncode:
        stop("Podman mount failed: " + r.stderr[-1800:])

    rootfs = Path(r.stdout.strip().splitlines()[-1])

    if not str(rootfs).startswith("/application1/podman/storage/overlay/"):
        stop("Unexpected rootfs path: " + str(rootfs))

    if not rootfs.is_mount():
        stop("Overlay mount not active: " + str(rootfs))

    if not (rootfs / "etc/passwd").is_file():
        stop("Mounted rootfs still missing etc/passwd")

    print("OVERLAY ROOTFS: MOUNTED")
    print("ETC/PASSWD: VERIFIED", flush=True)

    r = run(POD + ["start", NAME], timeout=100)
    if r.returncode:
        stop("Podman start failed: " + r.stderr[-2000:])

    print("EXISTING CONTAINER: STARTED", flush=True)
else:
    print("EXISTING CONTAINER: ALREADY RUNNING")

health = '''
import urllib.request
with urllib.request.urlopen(
    "http://127.0.0.1:8766/health", timeout=3
) as r:
    assert r.status == 200
'''

healthy = False
for _ in range(40):
    current = inspect()["State"]
    if current["Status"] != "running" or current.get("OOMKilled"):
        break
    r = run(POD + ["exec", NAME,
                   "/opt/venv/bin/python", "-B", "-c", health],
            timeout=12)
    if r.returncode == 0:
        healthy = True
        break
    time.sleep(3)

if not healthy:
    r = run(POD + ["logs", "--tail", "50", NAME])
    print((r.stdout + r.stderr)[-3500:])
    stop("Native health not ready")

print("NATIVE MAX HEALTH: PASS", flush=True)

print("\n=== TWO REAL NATIVE CTA REQUESTS ===", flush=True)

test = r'''
import json, urllib.request, urllib.error
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

fixture = Path(
    "/workspace/artifacts/v1.168-max/"
    "cta_native_adjusted_sanity_input.json"
)
assert fixture.is_file(), "Real CTA fixture missing"

payload = json.loads(fixture.read_text())
data = json.dumps(payload).encode()

def send(n):
    req = urllib.request.Request(
        "http://127.0.0.1:8766/v2/cta/predict",
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            status = r.status
            body = json.loads(r.read())
    except urllib.error.HTTPError as e:
        return n, e.code, False, e.read().decode(errors="replace")[:900]
    except Exception as e:
        return n, 0, False, str(e)

    obj = body.get("jsonData", {}) if isinstance(body, dict) else {}
    prediction = obj.get("prediction", {}) if isinstance(obj, dict) else {}
    offers = prediction.get("offerList") if isinstance(prediction, dict) else None

    return n, status, isinstance(offers, list), str(body)[:500]

with ThreadPoolExecutor(max_workers=2) as pool:
    results = list(pool.map(send, (1, 2)))

for n, status, valid, detail in results:
    print(f"REQUEST {n}: HTTP={status} VALID_CTA={valid}")
    if status != 200 or not valid:
        print("ERROR:", detail)

passed = all(status == 200 and valid
             for _, status, valid, _ in results)

print("NATIVE HTTP 2/2:", "PASS" if passed else "FAIL")
'''

r = run(POD + ["exec", "-i", "-e", "PYTHONDONTWRITEBYTECODE=1",
               NAME, "/opt/venv/bin/python", "-B", "-"],
        data=test, timeout=210)

print(r.stdout)
if r.returncode:
    print(r.stderr[-1500:])

http_pass = "NATIVE HTTP 2/2: PASS" in r.stdout

print("\n=== NEW MAX EXECUTION LOGS ===")
r = run(POD + ["logs", "--since", since, "--tail", "350", NAME])
lines = (r.stdout + r.stderr).splitlines()

relevant = [
    line for line in lines
    if re.search(r"batch.?2|batch.size|ENGINE_ID|EXECUT|"
                 r"Worker failed|TensorValue|Traceback|OOM", line, re.I)
]

for line in relevant[-35:]:
    print(line[:450])

print("\n=== FINAL RESULT ===")
c = inspect()
print("CONTAINER:", NAME)
print("STATE:", c["State"]["Status"])
print("OOM:", c["State"].get("OOMKilled"))
print("NATIVE HTTP:", "PASS" if http_pass else "FAIL")
print("ACTUAL BATCH COALESCING: REQUIRES EXPLICIT EXECUTION PROOF")
print("ORIGINAL DS/MAX: UNCHANGED")
print("NEW CLONES: NONE")
print("SOURCE FILES MODIFIED: NONE")
PY
