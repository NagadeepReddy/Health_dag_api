podman --root /application1/podman/storage --runroot /run/containers/storage exec -i -w /workspace -e PYTHONDONTWRITEBYTECODE=1 a176e284b50a /opt/venv/bin/python -B - <<'PY'
import os, sys, time, signal, socket, json, subprocess, threading
import urllib.request, urllib.error, collections
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

mx = Path("/workspace/artifacts/v1.168-max")
core = Path("/workspace/artifacts/v1.168/core-artifact")
stage = mx / "cta_native_batch2_release_candidate"
model = mx / "cta_native_model"
port = 18767

fixtures = [
    mx / "test-results/cta_max_tiles_smoketest_input.json",
    mx / "cta_native_adjusted_sanity_input.json"
]

required = [
    core / "pipeline.py",
    stage / "maxserve_cta_extension/cta_native_launcher.py",
    stage / "maxserve_cta_extension/cta_router.py",
    stage / "maxserve_cta_extension/cta_native_scheduler.py",
    model / "config.json",
    Path("/batch2/real_max_batch2_backend.py"),
    *fixtures
]

for p in required:
    if not p.is_file():
        raise SystemExit("STOP: Missing " + str(p))

def available_mb():
    return int(next(
        x.split()[1] for x in
        Path("/proc/meminfo").read_text().splitlines()
        if x.startswith("MemAvailable:")
    )) // 1024

if available_mb() < 12000:
    raise SystemExit("STOP: Insufficient available RAM")

disk = os.statvfs("/workspace")
if disk.f_bavail * disk.f_frsize < 20 * 1024**3:
    raise SystemExit("STOP: Insufficient workspace storage")

with socket.socket() as s:
    if s.connect_ex(("127.0.0.1", port)) == 0:
        raise SystemExit("STOP: Test port occupied")

env = os.environ.copy()
env.update({
    "PYTHONPATH": f"{stage}:{core}:/batch2:{mx}",
    "PYTHONDONTWRITEBYTECODE": "1",
    "HOME": "/tmp",
    "TMPDIR": "/tmp",
    "XDG_CACHE_HOME": "/tmp/cta_native_batch2_cache",
    "CUDA_VISIBLE_DEVICES": "",
    "MAX_SERVE_DISABLE_TELEMETRY": "1"
})

# Apply the API-selection correction only inside the
# isolated test process. Do not modify vendor/MAX files.
launcher = r'''
import sys, runpy
from pathlib import Path
from max.serve.config import Settings, APIType
from max.serve.api_server import ROUTES

original_init = Settings.__init__

def enable_kserve(self, *args, **kwargs):
    original_init(self, *args, **kwargs)
    if APIType.KSERVE not in self.api_types:
        self.api_types = list(self.api_types) + [APIType.KSERVE]

Settings.__init__ = enable_kserve

assert APIType.KSERVE in Settings().api_types

from maxserve_cta_extension.cta_router import register_cta_routes
register_cta_routes()

paths = [
    r.path for r in ROUTES[APIType.KSERVE].router.routes
]

assert "/v2/cta/probe" in paths
assert "/v2/cta/predict" in paths

print("KSERVE RUNTIME ACTIVATION: PASS", flush=True)

sys.argv = [
    "cta_native_launcher",
    "--port", "18767",
    "--model-path",
    "/workspace/artifacts/v1.168-max/cta_native_model",
    "--devices", "cpu",
    "--max-batch-size", "2"
]
runpy.run_module(
    "maxserve_cta_extension.cta_native_launcher",
    run_name="__main__"
)
'''

logs = collections.deque(maxlen=250)
stop = threading.Event()
server = None
success = False

try:
    server = subprocess.Popen(
        [sys.executable, "-B", "-u", "-c", launcher],
        cwd="/workspace",
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        start_new_session=True
    )

    def capture():
        for line in server.stdout:
            logs.append(line.rstrip())

    threading.Thread(target=capture, daemon=True).start()

    def memory_guard():
        while not stop.wait(2):
            if server.poll() is not None:
                return
            if available_mb() < 5500:
                logs.append("STOP: Memory reserve exhausted")
                try:
                    os.killpg(server.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                return

    threading.Thread(target=memory_guard, daemon=True).start()

    deadline = time.monotonic() + 150
    ready = False

    while time.monotonic() < deadline:
        if server.poll() is not None:
            raise RuntimeError("Native server exited during startup")

        with socket.socket() as s:
            s.settimeout(1)
            if s.connect_ex(("127.0.0.1", port)) == 0:
                ready = True
                break
        time.sleep(2)

    if not ready:
        raise RuntimeError("Native HTTP listener unavailable")

    print("NATIVE HTTP LISTENER: PASS", flush=True)

    # Confirm the actual mounted endpoint, not merely
    # the router source registration.
    probe = urllib.request.Request(
        f"http://127.0.0.1:{port}/v2/cta/probe",
        data=b"",
        method="POST"
    )

    with urllib.request.urlopen(probe, timeout=15) as r:
        if r.status != 200:
            raise RuntimeError("CTA probe HTTP status " + str(r.status))

    print("CTA NATIVE HTTP ROUTE: PASS", flush=True)

    bodies = [json.loads(p.read_text()) for p in fixtures]
    barrier = threading.Barrier(2)

    def send(i):
        barrier.wait(timeout=10)

        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/v2/cta/predict",
            data=json.dumps(bodies[i]).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=180) as r:
            status = r.status
            payload = json.loads(r.read(4 * 1024 * 1024))

        if status != 200 or not isinstance(payload, dict):
            raise RuntimeError(f"Request {i+1}: invalid HTTP response")

        if "error" in payload:
            raise RuntimeError(str(payload["error"]))

        data = payload.get("jsonData")
        if not isinstance(data, dict) or "prediction" not in data:
            raise RuntimeError(f"Request {i+1}: invalid CTA JSON")

        print(f"CTA RESPONSE {i+1}: PASS", flush=True)
        return payload

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(send, i) for i in range(2)]
        results = [f.result(timeout=195) for f in futures]

    assert len(results) == 2
    print("NATIVE CTA HTTP ACCEPTANCE: PASS", flush=True)
    success = True

except Exception as exc:
    print(
        "NATIVE HTTP ACCEPTANCE: NOT PASSED",
        type(exc).__name__,
        str(exc),
        flush=True
    )
    print("LAST NATIVE LOGS:", flush=True)
    print("\n".join(logs)[-6000:], flush=True)

finally:
    stop.set()

    if server is not None:
        if server.poll() is None:
            try:
                os.killpg(server.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(server.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            server.wait(timeout=5)

    print("TEST PROCESS STOPPED:",
          server is None or server.poll() is not None)
    print("CONTAINERS RESTARTED: NONE")
    print("ORIGINAL DS/MAX: UNCHANGED")

if not success:
    raise SystemExit(1)
PY
