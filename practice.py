
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import subprocess, json, time, urllib.request, urllib.error
from pathlib import Path

pod = [
    "podman",
    "--root", "/application1/podman/storage",
    "--runroot", "/run/containers/storage"
]
name = "cta-batch2-trace-8766-v2"
payload = Path(
    "/application1/sajjna8/rt-pzaas-cta-offers-v1/"
    "artifacts/v1.168-max/cta_native_adjusted_sanity_input.json"
)
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

def run(args):
    return subprocess.run(
        pod + args, capture_output=True, text=True, timeout=30
    )

def stop(message):
    raise SystemExit("STOP: " + message)

if not payload.is_file():
    stop("Saved CTA JSON missing")

data = payload.read_bytes()
try:
    assert isinstance(json.loads(data), dict)
except Exception:
    stop("CTA JSON invalid")

r = run(["inspect", name])
if r.returncode:
    stop("Isolated container missing")

info = json.loads(r.stdout)[0]
state = info["State"]["Status"]
memory = info.get("HostConfig", {}).get("Memory", 0)

if state != "exited":
    stop("Unexpected container state: " + state)

if memory < 5500000000:
    stop("6 GB container memory limit not confirmed")

available = next(
    int(x.split()[1]) for x in Path("/proc/meminfo").read_text().splitlines()
    if x.startswith("MemAvailable:")
)
if available < 8 * 1024 * 1024:
    stop("Insufficient available host memory")

def health(port):
    try:
        with opener.open(
            f"http://127.0.0.1:{port}/health", timeout=3
        ) as response:
            return response.status
    except Exception:
        return 0

if health(8765) != 200:
    stop("Original MAX health not confirmed")

if health(8766) == 200:
    stop("Port 8766 already serving")

print("ORIGINAL MAX 8765: HEALTHY", flush=True)
print("ISOLATED MEMORY LIMIT: 6 GB", flush=True)

r = run(["start", name])
if r.returncode:
    stop("Isolated start failed: " + r.stderr[-600:])

print("ISOLATED MAX: START REQUESTED", flush=True)

deadline = time.monotonic() + 120
ready = False

while time.monotonic() < deadline:
    if health(8766) == 200:
        ready = True
        break
    time.sleep(3)

if not ready:
    print("ISOLATED HEALTH: NOT READY")
else:
    print("ISOLATED HEALTH: HTTP 200", flush=True)
    print("REAL CTA JSON: SENDING", flush=True)

    request = urllib.request.Request(
        "http://127.0.0.1:8766/v2/cta/predict",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        start = time.monotonic()
        with opener.open(request, timeout=330) as response:
            result = json.load(response)
            status = response.status

        prediction = result.get("jsonData", {}).get("prediction")
        valid = isinstance(prediction, dict) and isinstance(
            prediction.get("offerList"), list
        )

        print("HTTP STATUS:", status)
        print("CTA JSON CONTRACT:", "PASS" if valid else "NOT VERIFIED")
        if valid:
            print("OFFERS:", len(prediction["offerList"]))
        else:
            print("RESPONSE KEYS:", list(result) if isinstance(result, dict) else type(result).__name__)
        print("LATENCY:", round(time.monotonic() - start, 2), "seconds")

    except urllib.error.HTTPError as e:
        print("HTTP ERROR:", e.code)
        print(e.read(1000).decode(errors="replace"))
    except Exception as e:
        print("REQUEST FAILED:", repr(e))

r = run(["inspect", name])
if r.returncode == 0:
    state = json.loads(r.stdout)[0]["State"]
    print("ISOLATED STATE:", state.get("Status"))
    print("OOM KILLED:", state.get("OOMKilled"))

if not ready or state.get("Status") != "running":
    logs = run(["logs", "--tail", "25", name])
    print("RECENT LOGS:")
    print((logs.stdout + logs.stderr)[-3000:])

print("ORIGINAL MAX HEALTH:", health(8765))
print("ORIGINAL DS: UNCHANGED")
PY
