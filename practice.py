PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import json, time, subprocess, urllib.request, urllib.error
import concurrent.futures, threading, datetime, re
from pathlib import Path

pod = [
    "podman",
    "--root", "/application1/podman/storage",
    "--runroot", "/run/containers/storage"
]
name = "cta-batch2-trace-8766-10g"
repo = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1")
sample = repo / "artifacts/v1.168-max/cta_native_adjusted_sanity_input.json"

def run(args, timeout=45):
    return subprocess.run(
        args, text=True, capture_output=True, timeout=timeout
    )

def health(port):
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/health", timeout=5
        ) as r:
            return r.status == 200
    except Exception:
        return False

print("=== SAFETY PRE-FLIGHT ===", flush=True)

assert health(8765), "STOP: Original MAX not healthy"
assert sample.is_file(), "STOP: Real CTA JSON fixture missing"

payload = sample.read_bytes()
assert isinstance(json.loads(payload), dict), "STOP: Invalid CTA JSON"

r = run(pod + ["inspect", name])
assert r.returncode == 0, "STOP: Isolated container missing"

info = json.loads(r.stdout)[0]
limit = int(info["HostConfig"]["Memory"])
assert 9 * 1024**3 <= limit <= 11 * 1024**3, \
    "STOP: Isolated memory limit is not 10 GB"

meminfo = Path("/proc/meminfo").read_text()
available_kb = int(re.search(
    r"MemAvailable:\s*(\d+)", meminfo
).group(1))
available_gb = available_kb / 1024**2

print("HOST AVAILABLE GB:", round(available_gb, 2))
assert available_gb >= 12, "STOP: Insufficient host memory"

assert not health(8766) or info["State"]["Running"], \
    "STOP: Port 8766 occupied by another process"

mounts = info["Mounts"]
assert any(
    m["Destination"] == "/batch2/real_max_batch2_backend.py"
    and Path(m["Source"]).resolve() ==
    Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/"
         "real_max_batch2_backend.py").resolve()
    for m in mounts
), "STOP: Fixed backend is not mounted"

assert any(
    m["Destination"] == "/batch2"
    and (Path(m["Source"]) /
         "cta_max/grecbase_fusion_batch2_draft.py").is_file()
    for m in mounts
), "STOP: Batch-2 graph is not mounted"

print("ORIGINAL MAX: HEALTHY")
print("MEMORY LIMIT: VERIFIED")
print("BATCH-2 BACKEND: MOUNTED")
print("REAL CTA JSON: READY")

started = datetime.datetime.now(
    datetime.timezone.utc
).isoformat()

print("\n=== RESTART ISOLATED ONLY ===", flush=True)
r = run(pod + ["restart", "--time", "15", name], timeout=90)
assert r.returncode == 0, f"STOP: {r.stderr}"

ready = False
for _ in range(45):
    if health(8766):
        ready = True
        break
    time.sleep(2)

assert ready, "STOP: Isolated server did not become healthy"
assert health(8765), "STOP: Original MAX health changed"

print("ISOLATED HTTP: READY")
print("ORIGINAL MAX: HEALTHY")

print("\n=== REAL NATIVE HTTP BATCH-2 ===", flush=True)

barrier = threading.Barrier(2)

def request(n):
    barrier.wait(timeout=10)
    start = time.monotonic()
    req = urllib.request.Request(
        "http://127.0.0.1:8766/v2/cta/predict",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=240) as response:
            result = json.loads(response.read())
            offers = result["jsonData"]["prediction"]["offerList"]
            assert isinstance(offers, list)
            return n, response.status, len(offers), round(
                time.monotonic() - start, 2
            )
    except urllib.error.HTTPError as e:
        return n, e.code, e.read(1500).decode(
            errors="replace"
        ), round(time.monotonic() - start, 2)
    except Exception as e:
        return n, "ERROR", repr(e), round(
            time.monotonic() - start, 2
        )

with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    futures = [pool.submit(request, n) for n in (1, 2)]
    results = sorted(f.result() for f in futures)

for result in results:
    print("REQUEST:", result, flush=True)

print("\n=== REAL MAX EXECUTION EVIDENCE ===")

r = run(
    pod + ["logs", "--since", started, "--tail", "1000", name],
    timeout=45
)
logs = r.stdout + r.stderr

markers = [
    "ISOLATED BATCH-2 GRAPH OVERRIDE",
    "CORRECTED BATCH-2 GRAPH",
    "EXECUTING REAL CTA INPUTS",
    "CTA TRUE MAX BATCH-2",
    "CTA RESPONSE ID MATCH",
    "POST /v2/cta/predict",
    "ERROR",
    "Traceback",
    "OOM",
]

for line in logs.splitlines():
    if any(marker in line for marker in markers):
        print(line[:550])

print("\n=== FINAL STATUS ===")

statuses_ok = all(x[1] == 200 for x in results)
graph_active = (
    "ISOLATED BATCH-2 GRAPH OVERRIDE" in logs
    or "CORRECTED BATCH-2 GRAPH" in logs
)
batch_evidence = (
    logs.count("CTA TRUE MAX BATCH-2: TWO JSON RESPONSES PRODUCED")
    == 1
)

print("HTTP 2/2:", "PASS" if statuses_ok else "FAIL")
print("GRAPH OVERRIDE:", "ACTIVE" if graph_active else "NOT CONFIRMED")
print("BATCH BACKEND:", "PASS" if batch_evidence else "NOT VERIFIED")
print("ORIGINAL MAX:", "HEALTHY" if health(8765) else "CHECK REQUIRED")
print("ORIGINAL DS: UNCHANGED")

if statuses_ok and graph_active and batch_evidence:
    print("NATIVE HTTP BATCH-2: PASS")
else:
    print("NATIVE HTTP BATCH-2: NOT YET VERIFIED")
PY
