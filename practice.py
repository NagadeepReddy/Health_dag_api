PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import subprocess, json, datetime

pod = [
    "podman",
    "--root", "/application1/podman/storage",
    "--runroot", "/run/containers/storage"
]
name = "cta-batch2-trace-8766-10g"

def run(args, timeout=45):
    return subprocess.run(
        args, capture_output=True, text=True, timeout=timeout
    )

r = run(pod + ["inspect", name])
assert r.returncode == 0, r.stderr
info = json.loads(r.stdout)[0]

assert info["State"]["Running"], "STOP: Container not running"
assert not info["State"]["OOMKilled"], "STOP: OOM detected"
assert 9 <= info["HostConfig"]["Memory"] / 1024**3 <= 11, \
    "STOP: Memory limit not verified"

print("=== NETWORK CHECK ===", flush=True)
print("NETWORK:", info["HostConfig"]["NetworkMode"])
print("PORTS:", info["NetworkSettings"].get("Ports"))
print("CONTAINER: RUNNING")
print("MEMORY: 10 GB VERIFIED")

started = datetime.datetime.now(
    datetime.timezone.utc
).isoformat()

inside = r'''
import json, urllib.request, urllib.error
import concurrent.futures, threading, time
from pathlib import Path

url = "http://127.0.0.1:8766"
opener = urllib.request.build_opener(
    urllib.request.ProxyHandler({})
)

print("=== INTERNAL MAX HEALTH ===", flush=True)
try:
    with opener.open(url + "/health", timeout=8) as r:
        print("INTERNAL HEALTH:", r.status, flush=True)
        assert r.status == 200
except Exception as e:
    print("STOP: INTERNAL HEALTH UNAVAILABLE:", repr(e), flush=True)
    raise SystemExit(2)

fixture = Path(
    "/workspace/artifacts/v1.168-max/"
    "cta_native_adjusted_sanity_input.json"
)
assert fixture.is_file(), "STOP: Real CTA fixture missing"

body = fixture.read_bytes()
assert isinstance(json.loads(body), dict)

print("REAL CTA FIXTURE: VERIFIED", flush=True)
print("=== TWO REAL NATIVE HTTP REQUESTS ===", flush=True)

barrier = threading.Barrier(2)

def predict(n):
    barrier.wait(timeout=10)
    req = urllib.request.Request(
        url + "/v2/cta/predict",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    t = time.monotonic()
    try:
        with opener.open(req, timeout=120) as r:
            data = json.loads(r.read())
            offers = data["jsonData"]["prediction"]["offerList"]
            assert isinstance(offers, list)
            return n, r.status, len(offers), round(
                time.monotonic()-t, 2
            )
    except urllib.error.HTTPError as e:
        return n, e.code, e.read(500).decode(
            errors="replace"
        ), round(time.monotonic()-t, 2)
    except Exception as e:
        return n, "FAIL", repr(e), round(
            time.monotonic()-t, 2
        )

with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    futures = [pool.submit(predict, n) for n in (1, 2)]
    results = sorted(f.result() for f in futures)

for x in results:
    print("REQUEST:", x, flush=True)

print("HTTP 2/2:",
      "PASS" if all(x[1] == 200 for x in results)
      else "FAIL", flush=True)
'''

print("\n=== RUNNING INSIDE EXISTING CONTAINER ===", flush=True)
try:
    r = run(
        pod + [
            "exec", name, "/opt/venv/bin/python",
            "-c", inside
        ],
        timeout=145
    )
    print(r.stdout, flush=True)
    if r.stderr:
        print(r.stderr[-2500:], flush=True)
    print("EXECUTION EXIT:", r.returncode)
except subprocess.TimeoutExpired:
    print("STOP: Internal validation exceeded 145 seconds")

print("\n=== ACTUAL MAX BACKEND EVIDENCE ===")
r = run(
    pod + ["logs", "--since", started, "--tail", "700", name]
)
logs = r.stdout + r.stderr

markers = [
    "CTA TRUE MAX BATCH-2",
    "ISOLATED BATCH-2 GRAPH",
    "CTA RESPONSE ID MATCH",
    "CTA WORKER RESPONSE IDS",
    "EXECUTING REAL CTA INPUTS",
    "ERROR",
    "Traceback",
    "OOM"
]

for line in logs.splitlines():
    if any(m in line for m in markers):
        print(line[:450])

count = logs.count(
    "CTA TRUE MAX BATCH-2: TWO JSON RESPONSES PRODUCED"
)
print("BATCH RESPONSE MARKER COUNT:", count)
print("SINGLE BATCH EXECUTION:",
      "EVIDENCE FOUND" if count == 1
      else "NOT VERIFIED")

print("ORIGINAL MAX: NOT RESTARTED")
print("ORIGINAL DS: UNCHANGED")
print("FILES MODIFIED: NONE")
PY
