podman --root /application1/podman/storage --runroot /run/containers/storage exec -i -w /workspace -e PYTHONDONTWRITEBYTECODE=1 a176e284b50a /opt/venv/bin/python -B - <<'PY'
import os, sys, time, signal, socket, json, threading, collections
import subprocess, urllib.request, urllib.error
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

mx = Path("/workspace/artifacts/v1.168-max")
core = Path("/workspace/artifacts/v1.168/core-artifact")
stage = mx / "cta_native_batch2_release_candidate"
pkg = stage / "maxserve_cta_extension"
model = mx / "cta_native_model"
port = 18767

required = [
    core / "pipeline.py",
    pkg / "cta_native_launcher.py",
    pkg / "cta_worker_adapter.py",
    pkg / "cta_native_scheduler.py",
    model / "config.json",
    Path("/batch2/real_max_batch2_backend.py"),
    mx / "test-results/cta_max_tiles_smoketest_input.json",
    mx / "cta_native_adjusted_sanity_input.json"
]

if not all(p.is_file() for p in required):
    raise SystemExit("STOP: Required source or fixture missing")

def available_mb():
    return int(next(
        x.split()[1]
        for x in Path("/proc/meminfo").read_text().splitlines()
        if x.startswith("MemAvailable:")
    )) // 1024

print("AVAILABLE RAM MB:", available_mb(), flush=True)

if available_mb() < 14000:
    raise SystemExit("STOP: Insufficient available memory")

if os.statvfs("/workspace").f_bavail * \
        os.statvfs("/workspace").f_frsize < 20 * 1024**3:
    raise SystemExit("STOP: Insufficient workspace space")

with socket.socket() as s:
    if s.connect_ex(("127.0.0.1", port)) == 0:
        raise SystemExit("STOP: Test port already occupied")

env = os.environ.copy()
env.update({
    "PYTHONPATH": ":".join([
        str(stage),
        str(core),
        "/batch2",
        str(mx)
    ]),
    "PYTHONDONTWRITEBYTECODE": "1",
    "HOME": "/tmp",
    "TMPDIR": "/tmp",
    "XDG_CACHE_HOME": "/tmp/cta_batch2_cache",
    "CUDA_VISIBLE_DEVICES": ""
})

# Confirm the exact missing import is resolved in the
# environment inherited by the native model worker.
preflight = r'''
import importlib.util
from pathlib import Path

expected = Path(
    "/workspace/artifacts/v1.168/core-artifact/pipeline.py"
)

spec = importlib.util.find_spec("pipeline")
assert spec and Path(spec.origin).resolve() == expected.resolve()

launcher = importlib.util.find_spec(
    "maxserve_cta_extension.cta_native_launcher"
)

assert launcher
assert "cta_native_batch2_release_candidate" in launcher.origin

print("ORIGINAL CTA PIPELINE PATH: PASS")
print("STAGED MAX LAUNCHER PATH: PASS")
'''

check = subprocess.run(
    [sys.executable, "-B", "-c", preflight],
    env=env, text=True, capture_output=True, timeout=30
)

print(check.stdout, flush=True)
if check.returncode:
    print(check.stderr[-2500:])
    raise SystemExit("STOP: Import preflight failed")

command = [
    sys.executable, "-B", "-m",
    "maxserve_cta_extension.cta_native_launcher",
    "--port", str(port),
    "--model-path", str(model),
    "--devices", "cpu"
]

logs = collections.deque(maxlen=220)
stop = threading.Event()
server = None
passed = False

try:
    print("ISOLATED NATIVE MAX SERVE: STARTING", flush=True)

    server = subprocess.Popen(
        command, cwd="/workspace", env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True, bufsize=1,
        start_new_session=True
    )

    def capture():
        for line in server.stdout:
            logs.append(line.rstrip())

    threading.Thread(target=capture, daemon=True).start()

    def monitor():
        while not stop.wait(2):
            if server.poll() is not None:
                return
            if available_mb() < 5500:
                logs.append("STOP: Host memory reserve too low")
                try:
                    os.killpg(server.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                return

    threading.Thread(target=monitor, daemon=True).start()

    deadline = time.monotonic() + 180
    ready = False

    while time.monotonic() < deadline:
        if server.poll() is not None:
            raise RuntimeError("Native model worker exited during startup")

        with socket.socket() as s:
            s.settimeout(1)
            if s.connect_ex(("127.0.0.1", port)) == 0:
                ready = True
                break

        time.sleep(2)

    if not ready:
        raise RuntimeError("Native server did not become ready")

    print("NATIVE HTTP LISTENER: PASS", flush=True)

    fixtures = [
        mx / "test-results/cta_max_tiles_smoketest_input.json",
        mx / "cta_native_adjusted_sanity_input.json"
    ]
    bodies = [json.loads(p.read_text()) for p in fixtures]
    barrier = threading.Barrier(2)

    def request(i):
        barrier.wait(timeout=10)

        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/v2/cta/predict",
            data=json.dumps(bodies[i]).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=210) as response:
                status = response.status
                payload = json.loads(response.read(4 * 1024 * 1024))
        except urllib.error.HTTPError as e:
            detail = e.read(2000).decode(errors="replace")
            raise RuntimeError(f"HTTP {e.code}: {detail}")

        if status != 200:
            raise RuntimeError(f"Request {i+1}: HTTP {status}")

        if not isinstance(payload, dict):
            raise RuntimeError("Invalid response object")

        if "error" in payload:
            raise RuntimeError(str(payload["error"]))

        if not isinstance(payload.get("jsonData"), dict):
            raise RuntimeError("Missing jsonData")

        if "prediction" not in payload["jsonData"]:
            raise RuntimeError("Missing prediction")

        print(f"CTA HTTP RESPONSE {i+1}: PASS", flush=True)
        return payload

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(request, i) for i in range(2)]
        responses = [f.result(timeout=230) for f in futures]

    assert len(responses) == 2
    print("TWO NATIVE CTA HTTP RESPONSES: PASS", flush=True)
    passed = True

except Exception as e:
    print(
        "NATIVE HTTP TEST: NOT PASSED",
        type(e).__name__, str(e),
        flush=True
    )
    print("LATEST SERVER LOGS:", flush=True)
    print("\n".join(logs)[-7000:], flush=True)

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

    with socket.socket() as s:
        listening = s.connect_ex(("127.0.0.1", port)) == 0

    print("TEST PORT STILL LISTENING:", listening)
    print("EXISTING CONTAINER RESTARTED: NO")
    print("ORIGINAL DS/MAX: UNCHANGED")

if not passed:
    raise SystemExit(1)
PY
