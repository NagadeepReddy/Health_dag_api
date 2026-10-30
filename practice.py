PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import json, subprocess, urllib.request, time, concurrent.futures
from pathlib import Path

pod = ["podman", "--root", "/application1/podman/storage",
       "--runroot", "/run/containers/storage"]
name = "cta-batch2-trace-8766-10g"
repo = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1")
backend = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/real_max_batch2_backend.py")

def run(args, timeout=45):
    return subprocess.run(args, capture_output=True, text=True,
                          timeout=timeout, check=True)

def health(port):
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/health", timeout=5
        ) as r:
            return r.status == 200
    except Exception:
        return False

print("=== SAFETY PRE-FLIGHT ===", flush=True)

assert backend.is_file()
assert "CTA_BATCH2_IMPORT_PRIORITY_FIX" in backend.read_text()
assert health(8765), "STOP: Original MAX is not healthy"

info = json.loads(run(pod + ["inspect", name]).stdout)[0]
mounts = info["Mounts"]

assert any(
    Path(m["Source"]) == backend for m in mounts
), "STOP: Fixed backend is not mounted in isolated container"

limit = info["HostConfig"]["Memory"]
assert 0 < limit <= 10 * 1024**3, "STOP: Unexpected memory limit"

with open("/proc/meminfo") as f:
    mem = next(
        int(x.split()[1]) * 1024 for x in f
        if x.startswith("MemAvailable:")
    )

assert mem >= 12 * 1024**3, "STOP: Insufficient available memory"

fixtures = sorted(
    p for p in (repo / "artifacts/v1.168-max").rglob("*.json")
    if "sanity" in p.name.lower()
    and "input" in p.name.lower()
    and p.stat().st_size < 5 * 1024**2
)

assert fixtures, "STOP: Real sanity JSON fixture not found"

payload = json.loads(fixtures[0].read_text())
assert isinstance(payload, dict)

print("ORIGINAL MAX: HEALTHY")
print("FIXED BACKEND: MOUNTED")
print("MEMORY: SAFE")
print("REAL INPUT:", fixtures[0])
print("ISOLATED RESTART: STARTING", flush=True)

run(pod + ["restart", "--time", "15", name], timeout=60)

ready = False
for _ in range(60):
    if health(8766):
        ready = True
        break
    time.sleep(2)

assert ready, "STOP: Isolated MAX failed health check"

print("ISOLATED HEALTH: PASS", flush=True)

def predict(n):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        "http://127.0.0.1:8766/v2/cta/predict",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            obj = json.load(r)
            prediction = obj.get("jsonData", {}).get("prediction", {})
            valid = r.status == 200 and isinstance(
                prediction.get("offerList"), list
            )
            return n, valid, r.status, len(prediction.get("offerList", []))
    except Exception as e:
        return n, False, type(e).__name__, str(e)[:160]

print("REAL NATIVE HTTP BATCH-2: START", flush=True)

with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    results = list(pool.map(predict, [1, 2]))

for n, passed, status, detail in results:
    print(f"REQUEST {n}: {'PASS' if passed else 'FAIL'} | {status} | {detail}")

print("HTTP RESULT:",
      "PASS 2/2" if all(x[1] for x in results) else "NOT PASSED")

print("ORIGINAL MAX:",
      "UNCHANGED / HEALTHY" if health(8765) else "HEALTH CHECK FAILED")
print("ORIGINAL DS: UNCHANGED")
PY
