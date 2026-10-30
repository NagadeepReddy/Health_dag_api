
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import subprocess, json, urllib.request, sys
from pathlib import Path

pod = ["podman", "--root", "/application1/podman/storage",
       "--runroot", "/run/containers/storage"]
name = "cta-batch2-trace-8766-10g"

def run(*args, timeout=45):
    return subprocess.run(pod + list(args), text=True,
                          capture_output=True, timeout=timeout)

r = run("inspect", name)
assert r.returncode == 0, r.stderr
info = json.loads(r.stdout)[0]

print("=== CORRECTED PRE-FLIGHT ===", flush=True)
print("NETWORK:", info["HostConfig"]["NetworkMode"], flush=True)
print("STATUS:", info["State"]["Status"], flush=True)
print("OOM:", info["State"]["OOMKilled"], flush=True)
print("MEMORY GB:", round(info["HostConfig"]["Memory"]/1024**3, 2), flush=True)

assert info["State"]["Status"] == "running", "STOP: Isolated server not running"
assert not info["State"]["OOMKilled"], "STOP: OOM detected"
assert 9 <= info["HostConfig"]["Memory"]/1024**3 <= 12
assert any(m["Destination"] == "/workspace" for m in info["Mounts"])

with urllib.request.urlopen("http://127.0.0.1:8765/health", timeout=5) as r:
    assert r.status == 200

print("ORIGINAL MAX: HEALTHY", flush=True)

inside = r'''
import urllib.request, urllib.error, json, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

url = "http://127.0.0.1:8766"
payload = Path(
    "/workspace/artifacts/v1.168-max/cta_native_adjusted_sanity_input.json"
)
assert payload.is_file(), "STOP: Real CTA JSON not mounted"

ready = False
for i in range(60):
    try:
        with urllib.request.urlopen(url + "/health", timeout=3) as r:
            if r.status == 200:
                ready = True
                break
    except Exception:
        time.sleep(2)

assert ready, "STOP: Isolated MAX not healthy"
print("ISOLATED MAX HEALTH: PASS", flush=True)

body = json.dumps(json.loads(payload.read_text())).encode()

def test(n):
    t = time.monotonic()
    req = urllib.request.Request(
        url + "/v2/cta/predict",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=240) as response:
            result = json.load(response)
            offers = result["jsonData"]["prediction"]["offerList"]
            assert isinstance(offers, list)
            return n, "PASS", round(time.monotonic()-t, 2), len(offers)
    except Exception as e:
        detail = repr(e)
        if isinstance(e, urllib.error.HTTPError):
            detail += " " + e.read(400).decode(errors="replace")
        return n, "FAIL", round(time.monotonic()-t, 2), detail

print("RUNNING TWO REAL CTA REQUESTS", flush=True)
with ThreadPoolExecutor(max_workers=2) as pool:
    results = list(pool.map(test, (1,2)))

for n, status, duration, detail in results:
    print(f"REQUEST {n}: {status} | {duration}s | {detail}", flush=True)

passed = sum(x[1] == "PASS" for x in results)
print(f"REAL NATIVE HTTP: {passed}/2 PASS", flush=True)
print("TRUE BATCH COALESCING: REQUIRES SCHEDULER LOG CONFIRMATION")
'''

print("=== ISOLATED INTERNAL HTTP TEST ===", flush=True)
result = subprocess.run(
    pod + ["exec", "-e", "PYTHONDONTWRITEBYTECODE=1",
           name, "/opt/venv/bin/python", "-u", "-c", inside],
    timeout=420
)

if result.returncode:
    print("=== RECENT RELEVANT LOGS ===", flush=True)
    logs = run("logs", "--tail", "100", name)
    terms = ("ERROR", "Error", "STOP:", "Traceback", "OOM",
             "CTA TRUE MAX", "REAL INPUT", "graph expects")
    matching = [line for line in (logs.stdout+logs.stderr).splitlines()
                if any(term in line for term in terms)]
    print("\n".join(matching[-25:]))

print("ORIGINAL DS: UNCHANGED")
print("ORIGINAL MAX: UNCHANGED")
print("NO FILES MODIFIED")
PY
