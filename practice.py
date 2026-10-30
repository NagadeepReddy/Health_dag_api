podman --root /application1/podman/storage \
--runroot /run/containers/storage \
exec -i -w /workspace \
-e PYTHONDONTWRITEBYTECODE=1 \
-e PYTHONUNBUFFERED=1 \
-e OTEL_SDK_DISABLED=true \
-e OTEL_METRICS_EXPORTER=none \
-e OTEL_TRACES_EXPORTER=none \
-e OTEL_LOGS_EXPORTER=none \
-e PYTHONPATH=/workspace/artifacts/v1.168-max/cta_native_batch2_release_candidate:/workspace/artifacts/v1.168/core-artifact:/batch2:/workspace/artifacts/v1.168-max \
0c95d4a8f887 /opt/venv/bin/python -B -u - <<'PY'
import os, sys, json, time, signal, socket, threading, subprocess
import urllib.request, urllib.error
from pathlib import Path
from collections import deque
from concurrent.futures import ThreadPoolExecutor

mx = Path("/workspace/artifacts/v1.168-max")
port = 18767
fixtures = [
    mx / "test-results/cta_max_tiles_smoketest_input.json",
    mx / "cta_native_adjusted_sanity_input.json",
]
required = [
    mx / "cta_native_model/config.json",
    mx / "cta_native_batch2_release_candidate/maxserve_cta_extension/cta_native_launcher.py",
    Path("/batch2/real_max_batch2_backend.py"),
    *fixtures,
]

for p in required:
    if not p.is_file():
        raise SystemExit("STOP: Missing " + str(p))

def memory():
    return int(Path("/sys/fs/cgroup/memory.current").read_text())

limit = int(Path("/sys/fs/cgroup/memory.max").read_text())
if limit - memory() < 5 * 1024**3:
    raise SystemExit("STOP: Insufficient container memory headroom")

with socket.socket() as sock:
    if sock.connect_ex(("127.0.0.1", port)) == 0:
        raise SystemExit("STOP: Test port already occupied")

bodies = [json.loads(p.read_text()) for p in fixtures]
assert bodies[0] != bodies[1], "Distinct requests required"

env = os.environ.copy()
env.update({
    "HOME": "/tmp",
    "TMPDIR": "/tmp",
    "XDG_CACHE_HOME": "/tmp/cta_batch2_cache",
    "HF_HOME": "/tmp/cta_batch2_cache",
    "TORCH_HOME": "/tmp/cta_batch2_cache",
    "CUDA_VISIBLE_DEVICES": "",
})

launch = (
    "from maxserve_cta_extension.cta_queue_compat import install;"
    "assert install();"
    "from maxserve_cta_extension.cta_native_launcher import main;"
    "main()"
)

cmd = [
    sys.executable, "-B", "-u", "-c", launch,
    "--port", str(port),
    "--model-path", str(mx / "cta_native_model"),
    "--devices", "cpu",
    "--max-batch-size", "2",
]

server = None
logs = deque(maxlen=1800)
stop = threading.Event()
passed = False

try:
    server = subprocess.Popen(
        cmd, cwd="/workspace", env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1, start_new_session=True
    )

    def capture():
        for line in server.stdout:
            if "telemetry.modular.com" not in line:
                logs.append(line.rstrip())

    threading.Thread(target=capture, daemon=True).start()

    def guard():
        while not stop.wait(2):
            if server.poll() is not None:
                return
            if memory() > limit * 0.80:
                logs.append("STOP: Memory safety guard triggered")
                try:
                    os.killpg(server.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                return

    threading.Thread(target=guard, daemon=True).start()

    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        if server.poll() is not None:
            raise RuntimeError("Native launcher exited during startup")
        with socket.socket() as sock:
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                break
        time.sleep(2)
    else:
        raise RuntimeError("Native listener did not start")

    print("NATIVE HTTP LISTENER: PASS", flush=True)

    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/v2/cta/probe",
        data=b"", method="POST"
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        assert r.status == 200

    print("NATIVE CTA ROUTE: PASS", flush=True)

    barrier = threading.Barrier(2)

    def send(i):
        barrier.wait(timeout=15)
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/v2/cta/predict",
            data=json.dumps(bodies[i]).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=505) as r:
                status = r.status
                output = json.loads(r.read(4 * 1024 * 1024))
        except urllib.error.HTTPError as e:
            raise RuntimeError(
                f"Request {i+1}: HTTP {e.code} "
                + e.read(700).decode(errors="replace")
            )

        if (
            status != 200
            or not isinstance(output, dict)
            or not isinstance(output.get("jsonData"), dict)
            or "prediction" not in output["jsonData"]
        ):
            raise RuntimeError(f"Request {i+1}: Invalid CTA response")

        print(f"CTA RESPONSE {i+1}: HTTP 200 PASS", flush=True)
        return output

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(send, i) for i in range(2)]
        responses = [f.result(timeout=520) for f in futures]

    assert len(responses) == 2
    print("TWO NATIVE CTA RESPONSES: PASS", flush=True)

    evidence = [
        x for x in logs
        if any(k in x.lower() for k in (
            "predict_batch", "real max batch",
            "batch dispatch", "response ids",
            "response queue send"
        ))
    ]

    print("BATCH EXECUTION EVIDENCE:")
    print("\n".join(evidence[-20:]) or "NOT LOGGED")
    passed = True

except Exception as e:
    print(
        "NATIVE BATCH-2: NOT PASSED",
        type(e).__name__, str(e), flush=True
    )
    relevant = [
        x for x in logs
        if any(k in x.lower() for k in (
            "cta", "batch", "queue", "worker",
            "error", "exception", "traceback",
            "msgspec", "memory", "timeout"
        ))
    ]
    print("RELEVANT LOGS:")
    print("\n".join(relevant[-60:])[-8500:], flush=True)

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

    print("ORIGINAL DS/MAX: UNCHANGED")
    print("WORKING NATIVE RELEASE: UNCHANGED")
    print("EXISTING CONTAINERS NOT RESTARTED")

if not passed:
    raise SystemExit(1)
PY
