podman --root /application1/podman/storage --runroot /run/containers/storage exec -i -w /workspace -e PYTHONDONTWRITEBYTECODE=1 a176e284b50a /opt/venv/bin/python -B - <<'PY'
import os, sys, time, signal, socket, json
import subprocess, threading, collections
import urllib.request, urllib.error
import concurrent.futures
from pathlib import Path

root = Path("/workspace/artifacts/v1.168-max")
stage_root = root / "cta_native_batch2_release_candidate"
stage = stage_root / "maxserve_cta_extension"
model = root / "cta_native_model"
backend = Path("/batch2/real_max_batch2_backend.py")

fixtures = [
    root / "test-results/cta_max_tiles_smoketest_input.json",
    root / "cta_native_adjusted_sanity_input.json"
]

required = [
    stage / "cta_native_launcher.py",
    stage / "cta_worker_adapter.py",
    stage / "cta_native_scheduler.py",
    model / "config.json",
    backend,
    *fixtures
]

if not all(p.is_file() for p in required):
    raise SystemExit("STOP: Required staged runtime file unavailable")

memory = lambda: int(next(
    x.split()[1]
    for x in Path("/proc/meminfo").read_text().splitlines()
    if x.startswith("MemAvailable:")
)) // 1024

free_gb = os.statvfs("/workspace")
free_gb = free_gb.f_bavail * free_gb.f_frsize / (1024**3)

print("AVAILABLE RAM MB:", memory(), flush=True)
print("WORKSPACE FREE GB:", round(free_gb, 1), flush=True)

if memory() < 14000 or free_gb < 20:
    raise SystemExit("STOP: Shared VM resource safety check failed")

port = 18767

with socket.socket() as sock:
    if sock.connect_ex(("127.0.0.1", port)) == 0:
        raise SystemExit("STOP: Isolated test port already occupied")

env = os.environ.copy()
env.update({
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONPATH": f"{stage_root}:/batch2:{root}",
    "HOME": "/tmp",
    "XDG_CACHE_HOME": "/tmp/cta_native_batch2_cache",
    "TMPDIR": "/tmp",
    "CUDA_VISIBLE_DEVICES": ""
})

command = [
    sys.executable, "-B", "-m",
    "maxserve_cta_extension.cta_native_launcher",
    "--port", str(port),
    "--model-path", str(model),
    "--devices", "cpu"
]

print("ISOLATED NATIVE MAX SERVE: STARTING", flush=True)

logs = collections.deque(maxlen=120)
process = subprocess.Popen(
    command,
    cwd="/workspace",
    env=env,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1,
    start_new_session=True
)

def capture_logs():
    for line in process.stdout:
        logs.append(line.rstrip("\n"))

threading.Thread(target=capture_logs, daemon=True).start()

stop_monitor = threading.Event()

def monitor_memory():
    while not stop_monitor.wait(2):
        if process.poll() is not None:
            return
        if memory() < 5500:
            logs.append("STOP: Shared VM memory reserve below 5500 MB")
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            return

threading.Thread(target=monitor_memory, daemon=True).start()

try:
    ready = False
    deadline = time.monotonic() + 180

    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("Native server exited during startup")

        with socket.socket() as sock:
            sock.settimeout(1)
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                ready = True
                break

        time.sleep(2)

    if not ready:
        raise RuntimeError("Native server startup did not complete")

    print("ISOLATED MAX SERVE LISTENER: PASS", flush=True)

    bodies = [json.loads(p.read_text()) for p in fixtures]

    def request(index):
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/v2/cta/predict",
            data=json.dumps(bodies[index]).encode(),
            headers={
                "Content-Type": "application/json",
                "X-CTA-Test-Request": f"batch2-{index+1}"
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=190) as response:
                status = response.status
                payload = json.loads(response.read(4 * 1024 * 1024))
        except urllib.error.HTTPError as exc:
            detail = exc.read(1500).decode(errors="replace")
            raise RuntimeError(
                f"Request {index+1}: HTTP {exc.code}: {detail}"
            )

        if (
            status != 200
            or not isinstance(payload, dict)
            or "error" in payload
            or not isinstance(payload.get("jsonData"), dict)
            or "prediction" not in payload["jsonData"]
        ):
            raise RuntimeError(
                f"Request {index+1}: invalid CTA response"
            )

        return status

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(request, i) for i in range(2)]

        for i, future in enumerate(futures, 1):
            status = future.result(timeout=210)
            print(
                f"NATIVE CTA HTTP RESPONSE {i}: {status} PASS",
                flush=True
            )

    print("TWO NATIVE CTA HTTP RESPONSES: PASS", flush=True)

except Exception as exc:
    print(
        "NATIVE HTTP ACCEPTANCE: NOT PASSED",
        type(exc).__name__,
        str(exc),
        flush=True
    )
    print("SERVER ERROR DETAILS:", flush=True)
    print("\n".join(logs)[-4500:], flush=True)

finally:
    stop_monitor.set()

    if process.poll() is None:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass

        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait(timeout=5)

    with socket.socket() as sock:
        still_listening = (
            sock.connect_ex(("127.0.0.1", port)) == 0
        )

    print("TEST PROCESS STOPPED:", process.poll() is not None)
    print("TEST PORT STILL LISTENING:", still_listening)
    print("EXISTING CONTAINER RESTARTED: NO")
    print("ORIGINAL DS/MAX: UNCHANGED")
PY
