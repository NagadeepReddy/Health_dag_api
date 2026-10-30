
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import subprocess, json, time, sys
from pathlib import Path

POD = [
    "podman",
    "--root", "/application1/podman/storage",
    "--runroot", "/run/containers/storage",
]
NAME = "cta-batch2-trace-8766-10g"
CANDIDATE = Path(
    "/application1/cta_max_true_batch_dev_20261028/"
    "batch2_candidate/cta_max"
)

def run(args, timeout=60, data=None):
    return subprocess.run(
        POD + args,
        input=data,
        capture_output=True,
        text=True,
        timeout=timeout,
    )

print("=== BATCH-2 SAFETY PRE-FLIGHT ===", flush=True)

r = run(["inspect", NAME])
assert r.returncode == 0, "STOP: Existing isolated container missing"
info = json.loads(r.stdout)[0]

mounts = info.get("Mounts", [])
assert any(
    m.get("Destination") == "/batch2"
    and "batch2_candidate" in m.get("Source", "")
    for m in mounts
), "STOP: Expected batch-2 mount missing"

limit = int(info.get("HostConfig", {}).get("Memory") or 0)
assert 9 * 1024**3 <= limit <= 11 * 1024**3, (
    "STOP: Expected 10 GB memory limit missing"
)

available = next(
    int(line.split()[1]) * 1024
    for line in Path("/proc/meminfo").read_text().splitlines()
    if line.startswith("MemAvailable:")
)

print("HOST AVAILABLE GB:", round(available / 1024**3, 2))
print("CONTAINER LIMIT GB:", round(limit / 1024**3, 2))

assert available >= 12 * 1024**3, (
    "STOP: Insufficient memory headroom"
)

assert (CANDIDATE / "grecbase_aux_features_max.py").is_file()
assert (CANDIDATE / "grecbase_fusion_batch2_draft.py").is_file()

print("CANDIDATE MOUNT: VERIFIED")
print("ORIGINAL MAX: NOT TARGETED")
print("ORIGINAL DS: UNCHANGED")

print("\n=== RESTART ISOLATED CONTAINER ===", flush=True)

r = run(["restart", "--time", "15", NAME], timeout=120)
assert r.returncode == 0, (
    "STOP: Isolated restart failed: " + r.stderr[-1000:]
)

print("ISOLATED RESTART: COMPLETED", flush=True)

client = r'''
import json, time, urllib.request, urllib.error
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

base = "http://127.0.0.1:8766"

fixture = Path(
    "/workspace/artifacts/v1.168-max/"
    "cta_native_adjusted_sanity_input.json"
)
assert fixture.is_file(), "STOP: Real CTA fixture missing"

payload = json.loads(fixture.read_text())
assert isinstance(payload, dict)

print("=== NATIVE MAX HEALTH ===", flush=True)

healthy = False
deadline = time.monotonic() + 150

while time.monotonic() < deadline:
    try:
        with urllib.request.urlopen(base + "/health", timeout=3) as r:
            if r.status == 200:
                healthy = True
                break
    except Exception:
        pass
    time.sleep(2)

assert healthy, "STOP: Isolated MAX health not ready"
print("HEALTH: 200", flush=True)

def send(n):
    start = time.monotonic()
    req = urllib.request.Request(
        base + "/v2/cta/predict",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=240) as r:
            status = r.status
            body = r.read().decode(errors="replace")
    except urllib.error.HTTPError as e:
        status = e.code
        body = e.read().decode(errors="replace")
    except Exception as e:
        return n, 0, str(e), round(time.monotonic()-start,2)

    return n, status, body, round(time.monotonic()-start,2)

print("=== TWO REAL CTA HTTP REQUESTS ===", flush=True)

with ThreadPoolExecutor(max_workers=2) as pool:
    results = list(pool.map(send, [1, 2]))

def has_offers(obj):
    if isinstance(obj, dict):
        return "offerList" in obj or any(
            has_offers(v) for v in obj.values()
        )
    if isinstance(obj, list):
        return any(has_offers(v) for v in obj)
    return False

passed = 0
schema_passed = 0

for n, status, body, seconds in results:
    print("REQUEST:", n, "HTTP:", status,
          "SECONDS:", seconds, flush=True)
    if status == 200:
        passed += 1
    try:
        response = json.loads(body)
        if has_offers(response):
            schema_passed += 1
        print("JSON KEYS:",
              list(response)[:15]
              if isinstance(response,dict) else type(response).__name__,
              flush=True)
    except Exception:
        pass
    if status != 200:
        print("ERROR BODY:", body[:1800], flush=True)

print("HTTP:", f"{passed}/2", flush=True)
print("CTA SCHEMA:", f"{schema_passed}/2", flush=True)

if passed != 2 or schema_passed != 2:
    raise SystemExit("NATIVE BATCH-2: NOT PASSED")

print("NATIVE HTTP 2/2: PASS", flush=True)
print("CTA RESPONSE SCHEMA 2/2: PASS", flush=True)
print("SINGLE MAX EXECUTE: REQUIRES LOG EVIDENCE", flush=True)
'''

print("\n=== EXECUTING NATIVE TEST ===", flush=True)

try:
    r = run([
        "exec", "-i",
        "--env", "PYTHONDONTWRITEBYTECODE=1",
        NAME, "/opt/venv/bin/python", "-"
    ], timeout=450, data=client)
except subprocess.TimeoutExpired:
    print("NATIVE TEST: TIMEOUT")
    r = None

if r is not None:
    print(r.stdout[-7000:])
    if r.stderr:
        print("TEST STDERR:", r.stderr[-1800:])

print("\n=== RELEVANT MAX LOGS ===", flush=True)
logs = run(["logs", "--tail", "700", NAME])
keywords = (
    "CTA", "BATCH", "EXECUT", "reshape",
    "error", "Error", "Exception",
    "worker failed", "OOM", "killed",
)
matching = [
    line for line in (logs.stdout + logs.stderr).splitlines()
    if any(k in line for k in keywords)
]
for line in matching[-35:]:
    print(line[:1600])

print("\n=== FINAL STATUS ===")
print("ORIGINAL MAX: UNCHANGED")
print("ORIGINAL DS: UNCHANGED")
print("SOURCE FILES MODIFIED: NONE")
if r is not None and r.returncode == 0:
    print("REAL NATIVE HTTP: PASS")
    print("SINGLE BATCH EXECUTION: CHECK LOG MARKERS")
else:
    print("REAL NATIVE HTTP: NOT PASSED")
    print("NEXT ROOT CAUSE: SEE ERROR BODY AND LOGS")
    sys.exit(1)
PY
