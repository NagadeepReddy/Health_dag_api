
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import json, subprocess, time
import urllib.request, urllib.error
from pathlib import Path

POD = ["podman", "--root", "/application1/podman/storage",
       "--runroot", "/run/containers/storage"]
NAME = "cta-batch2-trace-8766-10g"
URL = "http://127.0.0.1:8766"
PAYLOAD = Path(
    "/application1/sajjna8/rt-pzaas-cta-offers-v1/"
    "artifacts/v1.168-max/cta_native_adjusted_sanity_input.json"
)

def cmd(*args):
    return subprocess.run(
        POD + list(args), capture_output=True, text=True, timeout=30
    )

def state():
    r = cmd("inspect", NAME)
    if r.returncode:
        raise RuntimeError("Isolated container not found: " + r.stderr)
    return json.loads(r.stdout)[0]

def health(port):
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/health", timeout=3
        ) as r:
            return r.status == 200
    except Exception:
        return False

def logs():
    r = cmd("logs", "--tail", "100", NAME)
    lines = (r.stdout + r.stderr).splitlines()
    print("\n=== RECENT ISOLATED ERRORS ===", flush=True)
    keys = ("ERROR", "Error", "Traceback", "OOM", "Killed",
            "STOP", "FileNotFound", "ModuleNotFound", "MemoryError",
            "graph expects", "WORKER", "worker", "START")
    matches = [x for x in lines if any(k in x for k in keys)]
    print("\n".join(matches[-30:]) or "\n".join(lines[-25:]))

print("=== ISOLATED MAX RECOVERY ===", flush=True)
s = state()
st = s["State"]
limit = s.get("HostConfig", {}).get("Memory", 0) / 1024**3
free = int(next(
    x.split()[1] for x in Path("/proc/meminfo").read_text().splitlines()
    if x.startswith("MemAvailable:")
)) / 1024**2

print("STATUS:", st.get("Status"))
print("EXIT:", st.get("ExitCode"))
print("OOM:", st.get("OOMKilled"))
print("MEMORY LIMIT GB:", round(limit, 2))
print("HOST AVAILABLE GB:", round(free, 2))
print("WORKDIR:", s.get("Config", {}).get("WorkingDir"))
print("ORIGINAL MAX 8765:", "HEALTHY" if health(8765) else "UNAVAILABLE")

if not health(8765):
    raise SystemExit("STOP: Original MAX health unavailable")

if st.get("OOMKilled"):
    logs()
    raise SystemExit("STOP: OOM detected. Do not restart blindly.")

if not (9 <= limit <= 12) or free < 12:
    logs()
    raise SystemExit("STOP: Memory safety requirements not met.")

if st.get("Status") != "running":
    if st.get("Status") not in ("exited", "created") or st.get("ExitCode") not in (0, None):
        logs()
        raise SystemExit("STOP: Abnormal exit; examine errors.")
    print("RESTARTING ONLY:", NAME, flush=True)
    r = cmd("start", NAME)
    if r.returncode:
        logs()
        raise SystemExit("START FAILED: " + r.stderr.strip())

ready = False
for i in range(12):
    if health(8766):
        ready = True
        break
    if state()["State"].get("Status") != "running":
        break
    time.sleep(3)

if not ready:
    logs()
    print("FINAL STATE:", state()["State"])
    raise SystemExit("STOP: Port 8766 unavailable; request not sent.")

print("ISOLATED 8766 HEALTH: PASS", flush=True)

assert PAYLOAD.is_file(), "Real CTA JSON missing"
data = json.loads(PAYLOAD.read_text())

req = urllib.request.Request(
    URL + "/v2/cta/predict",
    data=json.dumps(data).encode(),
    headers={"Content-Type": "application/json"},
    method="POST"
)

try:
    with urllib.request.urlopen(req, timeout=240) as r:
        response = json.load(r)
        offers = response["jsonData"]["prediction"]["offerList"]
        assert isinstance(offers, list)
        print("REAL CTA HTTP: PASS")
        print("OFFER COUNT:", len(offers))
except urllib.error.HTTPError as e:
    print("HTTP ERROR:", e.code, e.read(1500).decode(errors="replace"))
    logs()
except Exception as e:
    print("REQUEST ERROR:", type(e).__name__, str(e))
    logs()

print("FINAL CONTAINER STATE:", state()["State"]["Status"])
print("ORIGINAL MAX: NOT RESTARTED")
print("ORIGINAL DS: UNCHANGED")
PY
