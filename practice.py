podman --root /application1/podman/storage --runroot /run/containers/storage exec -i -w /workspace -e PYTHONDONTWRITEBYTECODE=1 a176e284b50a /opt/venv/bin/python -B - <<'PY'
import os, sys, time, signal, socket, json, threading, subprocess
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

if not all(p.is_file() for p in required):
    raise SystemExit("STOP: Required file missing")

def available_mb():
    return int(next(
        x.split()[1]
        for x in Path("/proc/meminfo").read_text().splitlines()
        if x.startswith("MemAvailable:")
    )) // 1024

if available_mb() < 14000:
    raise SystemExit("STOP: Insufficient memory for isolated startup")

disk = os.statvfs("/workspace")
if disk.f_bavail * disk.f_frsize < 20 * 1024**3:
    raise SystemExit("STOP: Insufficient workspace storage")

with socket.socket() as s:
    if s.connect_ex(("127.0.0.1", port)) == 0:
        raise SystemExit("STOP: Test port already in use")

env = os.environ.copy()
env.update({
    "PYTHONPATH": f"{stage}:{core}:/batch2:{mx}",
    "MAX_SERVE_API_TYPES": '["openai","sagemaker","kserve"]',
    "PYTHONDONTWRITEBYTECODE": "1",
    "HOME": "/tmp",
    "TMPDIR": "/tmp",
    "XDG_CACHE_HOME": "/tmp/cta_native_batch2_cache",
    "CUDA_VISIBLE_DEVICES": ""
})

command = [
    sys.executable, "-B", "-m",
    "maxserve_cta_extension.cta_native_launcher",
    "--port", str(port),
    "--model-path", str(model),
    "--devices", "cpu",
    "--max-batch-size", "2"
]

logs = collections.deque(maxlen=250)
stop = threading.Event()
process = None
passed = False

try:
    print("CTA NATIVE KSERVE TEST: START", flush=True)
    print("KSERVE API: ENABLED", flush=True)
    print("BATCH SIZE: 2", flush=True)

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

    def read_logs():
        for line in process.stdout:
            logs.append(line.rstrip())

    threading.Thread(
        target=read_logs, daemon=True
    ).start()

    def memory_guard():
        while not stop.wait(2):
            if process.poll() is not None:
                return
            if available_mb() < 5500:
                logs.append("STOP: Memory safety threshold reached")
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                return

    threading.Thread(
        target=memory_guard, daemon=True
    ).start()

    deadline = time.monotonic() + 180

    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("Native MAX Serve exited during startup")

        with socket.socket() as s:
            s.settimeout(1)
            if s.connect_ex(("127.0.0.1", port)) == 0:
                break

        time.sleep(2)
    else:
        raise RuntimeError("Native HTTP listener not ready")

    print("NATIVE HTTP LISTENER: PASS", flush=True)

    # Confirm KServe is really mounted before inference.
    probe_url = f"http://127.0.0.1:{port}/v2/cta/probe"

    probe = urllib.request.Request(
        probe_url, data=b"", method="POST"
    )

    try:
        with urllib.request.urlopen(probe, timeout=15) as r:
            probe_status = r.status
            print("CTA KSERVE PROBE:", probe_status, flush=True)
            if probe_status != 200:
                raise RuntimeError("CTA route not active")
    except urllib.error.HTTPError as e:
        raise RuntimeError(
            f"CTA route returned HTTP {e.code}"
        )

    bodies = [json.loads(p.read_text()) for p in fixtures]
    barrier = threading.Barrier(2)

    def send_request(i):
        barrier.wait(timeout=10)

        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/v2/cta/predict",
            data=json.dumps(bodies[i]).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=210) as r:
                status = r.status
                response = json.loads(r.read(4 * 1024 * 1024))
        except urllib.error.HTTPError as e:
            detail = e.read(1200).decode(errors="replace")
            raise RuntimeError(f"HTTP {e.code}: {detail}")

        if status != 200:
            raise RuntimeError(f"Request {i+1}: HTTP {status}")

        if not isinstance(response, dict) or "error" in response:
            raise RuntimeError(f"Request {i+1}: Invalid response")

        if not isinstance(response.get("jsonData"), dict):
            raise RuntimeError(f"Request {i+1}: Missing jsonData")

        if "prediction" not in response["jsonData"]:
            raise RuntimeError(f"Request {i+1}: Missing prediction")

        print(f"CTA HTTP RESPONSE {i+1}: PASS", flush=True)
        return response

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(send_request, i) for i in range(2)]
        responses = [f.result(timeout=230) for f in futures]

    assert len(responses) == 2

    print("NATIVE CTA HTTP TWO RESPONSES: PASS", flush=True)
    passed = True

except Exception as e:
    print("NATIVE HTTP ACCEPTANCE: NOT PASSED", flush=True)
    print(type(e).__name__ + ":", str(e), flush=True)
    print("LAST SERVER LOGS:", flush=True)
    print("\n".join(logs)[-7000:], flush=True)

finally:
    stop.set()

    if process is not None:
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

    with socket.socket() as s:
        occupied = s.connect_ex(("127.0.0.1", port)) == 0

    print("TEST PORT STILL LISTENING:", occupied)
    print("CONTAINERS RESTARTED: NONE")
    print("ORIGINAL DS/MAX: UNCHANGED")

if not passed:
    raise SystemExit(1)
PY
