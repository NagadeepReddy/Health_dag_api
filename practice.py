podman --root /application1/podman/storage --runroot /run/containers/storage exec -i -w /workspace -e PYTHONDONTWRITEBYTECODE=1 a176e284b50a /opt/venv/bin/python -B - <<'PY'
import os, sys, time, signal, socket, json, hashlib
import subprocess, threading, collections
import urllib.request, urllib.error
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

mx = Path("/workspace/artifacts/v1.168-max")
stage = mx / "cta_native_batch2_release_candidate"
core = Path("/workspace/artifacts/v1.168/core-artifact")
model = mx / "cta_native_model"
port = 18767

fixtures = [
    mx / "test-results/cta_max_tiles_smoketest_input.json",
    mx / "cta_native_adjusted_sanity_input.json"
]

required = [
    core / "pipeline.py",
    stage / "maxserve_cta_extension/cta_native_launcher.py",
    stage / "maxserve_cta_extension/cta_queue_compat.py",
    stage / "maxserve_cta_extension/cta_spawn_worker.py",
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
        line.split()[1]
        for line in Path("/proc/meminfo").read_text().splitlines()
        if line.startswith("MemAvailable:")
    )) // 1024

if available_mb() < 12000:
    raise SystemExit("STOP: Insufficient memory")

disk = os.statvfs("/workspace")
if disk.f_bavail * disk.f_frsize < 20 * 1024**3:
    raise SystemExit("STOP: Insufficient workspace storage")

with socket.socket() as s:
    if s.connect_ex(("127.0.0.1", port)) == 0:
        raise SystemExit("STOP: Test port already occupied")

env = os.environ.copy()
env.update({
    "PYTHONPATH": f"{stage}:{core}:/batch2:{mx}",
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONUNBUFFERED": "1",
    "HOME": "/tmp",
    "TMPDIR": "/tmp",
    "XDG_CACHE_HOME": "/tmp/cta_batch2_cache",
    "HF_HOME": "/tmp/cta_batch2_cache",
    "TORCH_HOME": "/tmp/cta_batch2_cache",
    "CUDA_VISIBLE_DEVICES": ""
})

command = [
    sys.executable, "-B", "-u", "-m",
    "maxserve_cta_extension.cta_native_launcher",
    "--port", str(port),
    "--model-path", str(model),
    "--devices", "cpu",
    "--max-batch-size", "2"
]

server = None
stop = threading.Event()
logs = collections.deque(maxlen=1200)
success = False

try:
    print("NATIVE BATCH-2 FINAL HTTP TEST: START", flush=True)

    server = subprocess.Popen(
        command,
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

    def guard():
        while not stop.wait(2):
            if server.poll() is not None:
                return
            if available_mb() < 5500:
                logs.append("STOP: Memory reserve too low")
                try:
                    os.killpg(server.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                return

    threading.Thread(target=guard, daemon=True).start()

    deadline = time.monotonic() + 180
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

    probe = urllib.request.Request(
        f"http://127.0.0.1:{port}/v2/cta/probe",
        data=b"",
        method="POST"
    )

    with urllib.request.urlopen(probe, timeout=20) as r:
        assert r.status == 200

    print("NATIVE CTA HTTP ROUTE: PASS", flush=True)

    bodies = [json.loads(p.read_text()) for p in fixtures]
    print(
        "DISTINCT JSON REQUESTS:",
        bodies[0] != bodies[1],
        flush=True
    )

    barrier = threading.Barrier(2)

    def send(i):
        barrier.wait(timeout=15)
        started = time.monotonic()

        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/v2/cta/predict",
            data=json.dumps(bodies[i]).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=360) as r:
                status = r.status
                result = json.loads(r.read(4 * 1024 * 1024))
        except urllib.error.HTTPError as e:
            detail = e.read(1200).decode(errors="replace")
            raise RuntimeError(f"HTTP {e.code}: {detail}")

        if status != 200:
            raise RuntimeError(f"Request {i+1}: HTTP {status}")

        if not isinstance(result, dict) or "error" in result:
            raise RuntimeError(f"Request {i+1}: Invalid response")

        data = result.get("jsonData")
        if not isinstance(data, dict) or "prediction" not in data:
            raise RuntimeError(f"Request {i+1}: Missing CTA prediction")

        elapsed = round(time.monotonic() - started, 2)

        print(
            f"CTA HTTP RESPONSE {i+1}: PASS "
            f"({elapsed}s)",
            flush=True
        )

        return result

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(send, i) for i in range(2)]
        responses = [f.result(timeout=380) for f in futures]

    assert len(responses) == 2

    print("TWO NATIVE CTA HTTP RESPONSES: PASS", flush=True)

    evidence = [
        line for line in logs
        if any(term in line.upper() for term in (
            "PREDICT_BATCH",
            "BATCH DISPATCH",
            "REAL MAX BATCH",
            "MODEL.EXECUTE",
            "RESPONSE IDS",
            "RESPONSE QUEUE SEND"
        ))
    ]

    print("NATIVE BATCH EXECUTION EVIDENCE:")
    print("\n".join(evidence[-25:])[-4000:] or "NOT LOGGED")

    success = True

except Exception as e:
    print(
        "NATIVE BATCH-2 ACCEPTANCE: NOT PASSED",
        type(e).__name__,
        str(e),
        flush=True
    )

    relevant = [
        line for line in logs
        if any(word in line.lower() for word in (
            "cta", "batch", "worker", "queue",
            "traceback", "exception", "error",
            "validation", "msgspec"
        ))
        and "telemetry.modular.com" not in line.lower()
    ]

    print("RELEVANT SERVER LOGS:")
    print("\n".join(relevant[-65:])[-9000:], flush=True)

finally:
    stop.set()

    if server is not None:
        if server.poll() is None:
            try:
                os.killpg(server.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass

        try:
            server.wait(timeout=12)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(server.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            server.wait(timeout=5)

    print(
        "ISOLATED TEST PROCESS STOPPED:",
        server is None or server.poll() is not None
    )
    print("ORIGINAL DS/MAX: UNCHANGED")
    print("WORKING NATIVE RELEASE: UNCHANGED")
    print("CONTAINERS RESTARTED: NONE")

if not success:
    raise SystemExit(1)
PY
