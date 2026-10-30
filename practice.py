PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import subprocess, json, os, sys
from pathlib import Path

pod = ["podman", "--root", "/application1/podman/storage",
       "--runroot", "/run/containers/storage"]
old = "cta-batch2-trace-8766-10g"
new = "cta-batch2-verify-8766"
candidate = Path("/application1/cta_max_true_batch_dev_20261028/batch2_candidate")

def run(args, **kw):
    return subprocess.run(args, text=True, capture_output=True, **kw)

print("=== TARGETED RECOVERY ===", flush=True)

r = run(pod + ["inspect", old])
if r.returncode:
    sys.exit("STOP: Existing isolated container not found")

info = json.loads(r.stdout)[0]
state = info["State"]["Status"]
print("EXISTING STATE:", state)

if state == "running":
    sys.exit("STOP: Existing container running; do not duplicate")

if info["HostConfig"]["Memory"] != 10737418240:
    sys.exit("STOP: 10 GB limit not verified")

mounts = info["Mounts"]
if not any(
    m["Destination"] == "/batch2"
    and Path(m["Source"]).resolve() == candidate.resolve()
    for m in mounts
):
    sys.exit("STOP: Candidate mount mismatch")

for f in ("grecbase_aux_features_max.py",
          "grecbase_fusion_batch2_draft.py"):
    if not (candidate / "cta_max" / f).is_file():
        sys.exit("STOP: Batch-2 candidate file missing: " + f)

mem = next(int(x.split()[1]) for x in
    Path("/proc/meminfo").read_text().splitlines()
    if x.startswith("MemAvailable:"))

disk = os.statvfs("/application1/podman/storage")
free_gb = disk.f_bavail * disk.f_frsize / 1024**3

if mem < 12 * 1024 * 1024 or free_gb < 5:
    sys.exit("STOP: Insufficient host memory or storage")

if run(pod + ["container", "exists", new]).returncode == 0:
    sys.exit("STOP: Validation container already exists")

print("SAFETY: PASS")
print("SAVED PATCHES: PRESENT")
print("CLONING ISOLATED CONFIGURATION", flush=True)

r = run(pod + [
    "container", "clone", "--name", new, "--run", old
], timeout=90)

if r.returncode:
    print("CLONE FAILED:", r.stderr[-1800:])
    sys.exit(1)

print("FRESH ISOLATED CONTAINER: STARTED", flush=True)

test = r'''
import json, time, urllib.request, urllib.error
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

base = "http://127.0.0.1:8766"

for attempt in range(80):
    try:
        with urllib.request.urlopen(base + "/health", timeout=2) as r:
            if r.status == 200:
                break
    except Exception:
        pass
    time.sleep(1)
else:
    raise SystemExit("STOP: Isolated health not ready")

print("ISOLATED HEALTH: PASS", flush=True)

p = Path("/workspace/artifacts/v1.168-max/cta_native_adjusted_sanity_input.json")
if not p.is_file():
    raise SystemExit("STOP: Real CTA fixture unavailable")

payload = p.read_bytes()
json.loads(payload)

def request(n):
    req = urllib.request.Request(
        base + "/v2/cta/predict",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            body = r.read()
            obj = json.loads(body)
            if not isinstance(obj, dict) or "error" in obj:
                return n, False, str(obj)[:700]
            return n, r.status == 200, "HTTP 200 / JSON"
    except urllib.error.HTTPError as e:
        return n, False, "HTTP %s %s" % (
            e.code, e.read(1200).decode(errors="replace"))
    except Exception as e:
        return n, False, repr(e)

with ThreadPoolExecutor(max_workers=2) as pool:
    results = list(pool.map(request, [1, 2]))

for n, passed, detail in results:
    print("REQUEST", n, "PASS" if passed else "FAIL", detail, flush=True)

print("HTTP 2/2:", "PASS" if all(x[1] for x in results)
      else "NOT PASSED", flush=True)
'''

try:
    r = subprocess.run(
        pod + ["exec", "-i", new, "/opt/venv/bin/python", "-B", "-c", test],
        text=True, capture_output=True, timeout=210
    )
    print(r.stdout)
    if r.returncode:
        print("VALIDATION ERROR:", r.stderr[-1200:])
except subprocess.TimeoutExpired:
    print("VALIDATION: TIMED OUT")

logs = run(pod + ["logs", "--tail", "150", new], timeout=20)
lines = (logs.stdout + logs.stderr).splitlines()
relevant = [
    s for s in lines if any(
        x in s.lower() for x in (
            "reshape", "error", "batch", "response id match",
            "worker failed", "oom", "traceback"
        )
    )
]

print("=== BACKEND EVIDENCE ===")
print("\n".join(relevant[-18:]) or "NO BATCH MARKERS FOUND")
print("ORIGINAL MAX: NOT RESTARTED")
print("ORIGINAL DS: UNCHANGED")
print("EXISTING CONTAINER: PRESERVED")
PY
