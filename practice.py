
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import json, subprocess, time, concurrent.futures
import urllib.request, urllib.error
from pathlib import Path

repo = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1")
base = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")
name = "cta-batch2-trace-8766-10g"
pod = ["podman", "--root", "/application1/podman/storage",
       "--runroot", "/run/containers/storage"]

def cmd(*args):
    return subprocess.run(pod + list(args), capture_output=True,
                          text=True, timeout=45)

def health(port):
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/health", timeout=3
        ) as response:
            return response.status == 200
    except Exception:
        return False

def logs():
    result = cmd("logs", "--tail", "200", name)
    lines = (result.stdout + result.stderr).splitlines()
    keys = ("ERROR", "Error", "STOP:", "OOM", "Killed",
            "fn_norm", "Traceback", "CTA TRUE MAX",
            "CTA HTTP", "Uvicorn running")
    selected = [x for x in lines if any(k in x for k in keys)]
    print("\n=== TARGETED WORKER LOGS ===")
    print("\n".join(selected[-30:] or lines[-15:]))

print("=== PRE-FLIGHT ===", flush=True)
assert health(8765), "STOP: Original MAX unhealthy"

adapter = base / "native_batch2_cached_overlay/cta_worker_adapter.py"
fixture = repo / "artifacts/v1.168-max/cta_native_adjusted_sanity_input.json"
assert adapter.is_file() and fixture.is_file(), "STOP: Missing source"
assert "# CTA_WORKER_CWD_FIX_V1" in adapter.read_text(), \
       "STOP: Existing CWD fix missing"

r = cmd("inspect", name)
assert r.returncode == 0, "STOP: Isolated container missing"
info = json.loads(r.stdout)[0]
state = info["State"]

assert info["HostConfig"]["NetworkMode"] == "host"
assert 9 <= info["HostConfig"]["Memory"] / 1024**3 <= 12
assert not state.get("OOMKilled"), "STOP: Previous OOM"
assert any(m["Destination"] == "/workspace" and
           m["Source"] == str(repo) for m in info["Mounts"])

if state["Status"] != "running":
    assert state["Status"] in ("exited", "created"), \
           "STOP: Unexpected container state"
    mem = next(int(x.split()[1])
               for x in Path("/proc/meminfo").read_text().splitlines()
               if x.startswith("MemAvailable:"))
    assert mem > 12 * 1024**2, "STOP: Insufficient available RAM"
    print("RESTARTING ISOLATED CONTAINER ONCE", flush=True)
    r = cmd("start", name)
    assert r.returncode == 0, r.stderr
else:
    print("EXISTING ISOLATED CONTAINER: REUSED", flush=True)

print("CHECKING MAX READINESS", flush=True)
deadline = time.monotonic() + 180

while not health(8766):
    s = json.loads(cmd("inspect", name).stdout)[0]["State"]
    if s["Status"] != "running" or s.get("OOMKilled"):
        logs()
        raise SystemExit("STOP: Isolated worker stopped")
    if time.monotonic() >= deadline:
        logs()
        raise SystemExit("STOP: Isolated MAX not ready")
    time.sleep(5)

print("ISOLATED MAX HEALTH: PASS", flush=True)

body = json.dumps(json.loads(fixture.read_text())).encode()

def test(n):
    start = time.monotonic()
    request = urllib.request.Request(
        "http://127.0.0.1:8766/v2/cta/predict",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(request, timeout=240) as r:
            result = json.load(r)
            offers = result["jsonData"]["prediction"]["offerList"]
            assert isinstance(offers, list)
            return n, "PASS", round(time.monotonic()-start, 2), len(offers)
    except Exception as e:
        detail = repr(e)
        if isinstance(e, urllib.error.HTTPError):
            detail += " " + e.read(500).decode(errors="replace")
        return n, "FAIL", round(time.monotonic()-start, 2), detail

print("SENDING TWO CONCURRENT REAL CTA REQUESTS", flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    results = list(pool.map(test, (1, 2)))

for n, status, elapsed, detail in results:
    print(f"REQUEST {n}: {status} | {elapsed}s | {detail}", flush=True)

if all(x[1] == "PASS" for x in results):
    print("REAL CTA NATIVE HTTP: 2/2 PASS")
    print("BATCH COALESCING: STILL REQUIRES SCHEDULER EVIDENCE")
else:
    print("REAL CTA NATIVE HTTP: NOT YET PASSING")
    logs()

print("ORIGINAL MAX: UNCHANGED")
print("ORIGINAL DS: UNCHANGED")
print("NO FILES MODIFIED")
PY
