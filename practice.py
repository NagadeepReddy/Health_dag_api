
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import subprocess, json, time, os, urllib.request, urllib.error
from pathlib import Path

P = ["podman", "--root", "/application1/podman/storage",
     "--runroot", "/run/containers/storage"]
SRC = "cta-batch2-trace-8766-v2"
NEW = "cta-batch2-trace-8766-10g"
BASE = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1")
DATA = BASE / "artifacts/v1.168-max/cta_native_adjusted_sanity_input.json"
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

def run(*args):
    return subprocess.run(P + list(args), capture_output=True,
                          text=True, timeout=60)

def stop(message):
    raise SystemExit("STOP: " + message)

def inspect(name):
    r = run("inspect", name)
    if r.returncode:
        stop("Cannot inspect " + name)
    return json.loads(r.stdout)[0]

def health(port):
    try:
        with opener.open("http://127.0.0.1:%s/health" % port,
                         timeout=5) as r:
            return r.status
    except Exception:
        return 0

mem = next(int(x.split()[1]) for x in
           Path("/proc/meminfo").read_text().splitlines()
           if x.startswith("MemAvailable:")) / 1048576
disk = os.statvfs("/application1")
free = disk.f_bavail * disk.f_frsize / 1073741824

print("HOST AVAILABLE GB:", round(mem, 2))
print("APPLICATION1 FREE GB:", round(free, 2))

if mem < 16 or free < 3:
    stop("Host resource safety gate failed")

if health(8765) != 200:
    stop("Original MAX unhealthy")

if health(8766) != 0:
    stop("Port 8766 is occupied")

if not DATA.is_file():
    stop("CTA sample missing")

original = inspect(SRC)
if original["State"]["Status"] == "running":
    stop("Old isolated container still running")

if run("container", "exists", NEW).returncode == 0:
    stop("New isolated container name already exists")

print("ORIGINAL MAX: HEALTHY")
print("CLONING ISOLATED CONTAINER", flush=True)

r = run("container", "clone",
        "--memory", "10g",
        "--memory-swap", "11g",
        SRC, NEW)
if r.returncode:
    stop("Clone failed: " + r.stderr[-600:])

new = inspect(NEW)
limit = new["HostConfig"]["Memory"]
print("NEW MEMORY LIMIT GB:", round(limit / 1073741824, 2))

if limit != 10 * 1073741824:
    stop("Clone memory limit not verified")

r = run("start", NEW)
if r.returncode:
    stop("Start failed: " + r.stderr[-600:])

print("ISOLATED SERVER: STARTED", flush=True)

ready = False
for i in range(60):
    if health(8766) == 200:
        ready = True
        break
    if inspect(NEW)["State"]["Status"] != "running":
        break
    time.sleep(3)

if ready:
    print("ISOLATED HEALTH: 200", flush=True)
    print("REAL CTA HTTP: SENDING", flush=True)

    req = urllib.request.Request(
        "http://127.0.0.1:8766/v2/cta/predict",
        data=DATA.read_bytes(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        start = time.monotonic()
        with opener.open(req, timeout=320) as response:
            code = response.status
            result = json.load(response)

        prediction = result.get("jsonData", {}).get("prediction", {})
        passed = code == 200 and isinstance(
            prediction.get("offerList"), list
        )

        print("HTTP:", code)
        print("CTA JSON:", "PASS" if passed else "NOT VERIFIED")
        print("LATENCY:", round(time.monotonic()-start, 2))

    except urllib.error.HTTPError as e:
        print("HTTP:", e.code)
        print("ERROR:", e.read(500).decode(errors="replace"))
    except Exception as e:
        print("HTTP ERROR:", repr(e))
else:
    print("ISOLATED HEALTH: FAILED")

state = inspect(NEW)["State"]
print("CONTAINER STATE:", state["Status"])
print("OOM KILLED:", state.get("OOMKilled"))
print("ORIGINAL MAX HEALTH:", health(8765))
print("ORIGINAL DS: UNCHANGED")
print("OLD ISOLATED CONTAINER: PRESERVED")

if state["Status"] != "running" or state.get("OOMKilled"):
    r = run("logs", "--tail", "25", NEW)
    print("LAST LOGS:", (r.stdout+r.stderr)[-1800:])
PY
