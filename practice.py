
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import subprocess, json, time, urllib.request, urllib.error
from pathlib import Path

P = ["podman", "--root", "/application1/podman/storage",
     "--runroot", "/run/containers/storage"]
N = "cta-batch2-trace-8766-v2"
BACKEND = "/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/real_max_batch2_backend.py"
JSON = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max/cta_native_adjusted_sanity_input.json")
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

def cmd(*args):
    return subprocess.run(P + list(args), text=True,
                          capture_output=True, timeout=45)

def stop(msg):
    raise SystemExit("STOP: " + msg)

def health(port):
    try:
        with opener.open(f"http://127.0.0.1:{port}/health", timeout=4) as r:
            return r.status
    except Exception:
        return 0

def inspect():
    r = cmd("inspect", N)
    if r.returncode:
        stop("Isolated container not found")
    return json.loads(r.stdout)[0]

i = inspect()
if i.get("Name", "").lstrip("/") != N:
    stop("Container identity mismatch")

mounts = i.get("Mounts") or []
if not any(m.get("Source") == BACKEND for m in mounts):
    stop("Expected isolated backend mount not confirmed")

available = next(
    int(line.split()[1]) for line in Path("/proc/meminfo").read_text().splitlines()
    if line.startswith("MemAvailable:")
) / 1048576

print("HOST AVAILABLE GB:", round(available, 2), flush=True)

if available < 16:
    stop("Insufficient safe host memory for 10 GB test")

if health(8765) != 200:
    stop("Original MAX 8765 not healthy")

if not JSON.is_file():
    stop("Saved CTA request missing")

data = JSON.read_bytes()
try:
    assert isinstance(json.loads(data), dict)
except Exception:
    stop("Saved CTA request is invalid")

print("ORIGINAL MAX: HEALTHY", flush=True)

if i["State"]["Status"] == "running":
    r = cmd("stop", "--time", "15", N)
    if r.returncode:
        stop("Could not stop isolated container: " + r.stderr[-300:])

r = cmd("update", "--memory", "10g",
        "--memory-swap", "10g", N)
if r.returncode:
    stop("Memory update failed: " + r.stderr[-500:])

i = inspect()
if i["HostConfig"]["Memory"] < 10 * 1024**3:
    stop("10 GB memory limit not confirmed")

print("ISOLATED MEMORY LIMIT: 10 GB", flush=True)

r = cmd("start", N)
if r.returncode:
    stop("Isolated restart failed: " + r.stderr[-500:])

print("ISOLATED MAX: RESTARTED", flush=True)

ready = False
for _ in range(40):
    if health(8766) == 200:
        ready = True
        break
    if inspect()["State"]["Status"] != "running":
        break
    time.sleep(3)

if ready:
    print("ISOLATED HEALTH: 200", flush=True)
    print("REAL CTA REQUEST: START", flush=True)
    req = urllib.request.Request(
        "http://127.0.0.1:8766/v2/cta/predict",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        start = time.monotonic()
        with opener.open(req, timeout=320) as r:
            status = r.status
            result = json.load(r)
        prediction = result.get("jsonData", {}).get("prediction", {})
        passed = (
            status == 200
            and isinstance(prediction, dict)
            and isinstance(prediction.get("offerList"), list)
        )
        print("HTTP STATUS:", status)
        print("CTA JSON CONTRACT:", "PASS" if passed else "NOT VERIFIED")
        if passed:
            print("OFFERS:", len(prediction["offerList"]))
        print("LATENCY:", round(time.monotonic()-start, 2))
    except urllib.error.HTTPError as e:
        print("HTTP STATUS:", e.code)
        print("ERROR:", e.read(600).decode(errors="replace"))
    except Exception as e:
        print("REQUEST ERROR:", repr(e))
else:
    print("ISOLATED HEALTH: NOT READY")

i = inspect()
print("ISOLATED STATE:", i["State"]["Status"])
print("OOM FLAG:", i["State"].get("OOMKilled"))

if not ready or i["State"].get("OOMKilled"):
    r = cmd("logs", "--tail", "35", N)
    print("RECENT WORKER LOGS:")
    print((r.stdout + r.stderr)[-2500:])

print("ORIGINAL MAX HEALTH:", health(8765))
print("ORIGINAL DS: UNCHANGED")
PY
