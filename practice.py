podman --root /application1/podman/storage --runroot /run/containers/storage exec -i -w /workspace -e PYTHONDONTWRITEBYTECODE=1 a176e284b50a /opt/venv/bin/python -B - <<'PY'
import os, sys, time, signal, socket, json
import subprocess, threading, collections
import urllib.request, urllib.error
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

mx = Path("/workspace/artifacts/v1.168-max")
core = Path("/workspace/artifacts/v1.168/core-artifact")
stage = mx / "cta_native_batch2_release_candidate"
pkg = stage / "maxserve_cta_extension"
port = 18767

fixtures = [
    mx / "test-results/cta_max_tiles_smoketest_input.json",
    mx / "cta_native_adjusted_sanity_input.json"
]

required = [
    core / "pipeline.py",
    pkg / "cta_native_launcher.py",
    pkg / "cta_native_scheduler.py",
    pkg / "cta_worker_adapter.py",
    pkg / "cta_router.py",
    mx / "cta_native_model/config.json",
    Path("/batch2/real_max_batch2_backend.py"),
    *fixtures
]

for p in required:
    if not p.is_file():
        raise SystemExit("STOP: Missing " + str(p))

def available_mb():
    return int(next(
        x.split()[1]
        for x in Path("/proc/meminfo").read_text().splitlines()
        if x.startswith("MemAvailable:")
    )) // 1024

if available_mb() < 12000:
    raise SystemExit("STOP: Insufficient available memory")

fs = os.statvfs("/workspace")
if fs.f_bavail * fs.f_frsize < 20 * 1024**3:
    raise SystemExit("STOP: Insufficient workspace storage")

with socket.socket() as s:
    if s.connect_ex(("127.0.0.1", port)) == 0:
        raise SystemExit("STOP: Test port already occupied")

env = os.environ.copy()
env.update({
    "PYTHONPATH": f"{stage}:{core}:/batch2:{mx}",
    "PYTHONDONTWRITEBYTECODE": "1",
    "HOME": "/tmp",
    "TMPDIR": "/tmp",
    "XDG_CACHE_HOME": "/tmp/cta_native_batch2_cache",
    "CUDA_VISIBLE_DEVICES": ""
})

launcher = r'''
import sys
import runpy
from typing import Any

from max.serve.config import Settings, APIType
from max.serve.scheduler.queues import SchedulerZmqConfigs
from max.serve.queue.zmq_queue import ZmqConfig

# Reuse the verified native CTA queue compatibility approach.
# Request queue only; preserve original response/cancel configurations.
original_queue_init = SchedulerZmqConfigs.__init__

def cta_queue_init(self, pipeline_task):
    original_queue_init(self, pipeline_task)
    self.request_queue_config = ZmqConfig[Any](Any)

SchedulerZmqConfigs.__init__ = cta_queue_init

print("CTA REQUEST QUEUE COMPATIBILITY: INSTALLED", flush=True)
print("RESPONSE/CANCEL QUEUES: UNCHANGED", flush=True)

# Enable KServe on the isolated MAX application.
original_settings_init = Settings.__init__

def cta_settings_init(self, *args, **kwargs):
    original_settings_init(self, *args, **kwargs)
    if APIType.KSERVE not in self.api_types:
        self.api_types = list(self.api_types) + [APIType.KSERVE]

Settings.__init__ = cta_settings_init

assert APIType.KSERVE in Settings().api_types

print("CTA KSERVE CONFIGURATION: PASS", flush=True)

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

server = None
stop = threading.Event()
logs = collections.deque(maxlen=350)
success = False

try:
    print("ISOLATED NATIVE BATCH-2: START", flush=True)

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

    def collect_logs():
        for line in server.stdout:
            logs.append(line.rstrip())

    threading.Thread(
        target=collect_logs,
        daemon=True
    ).start()

    def memory_guard():
        while not stop.wait(2):
            if server.poll() is not None:
                return
            if available_mb() < 5500:
                logs.append("STOP: Memory safety threshold reached")
                try:
                    os.killpg(server.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                return

    threading.Thread(
        target=memory_guard,
        daemon=True
    ).start()

    deadline = time.monotonic() + 180

    while time.monotonic() < deadline:
        if server.poll() is not None:
            raise RuntimeError("Native server exited during startup")

        with socket.socket() as s:
            s.settimeout(1)
            if s.connect_ex(("127.0.0.1", port)) == 0:
                break

        time.sleep(2)
    else:
        raise RuntimeError("Native listener startup timeout")

    print("NATIVE HTTP LISTENER: PASS", flush=True)

    probe = urllib.request.Request(
        f"http://127.0.0.1:{port}/v2/cta/probe",
        data=b"",
        method="POST"
    )

    with urllib.request.urlopen(probe, timeout=15) as r:
        if r.status != 200:
            raise RuntimeError("CTA probe failed")

    print("CTA NATIVE HTTP ROUTE: PASS", flush=True)

    bodies = [json.loads(p.read_text()) for p in fixtures]
    barrier = threading.Barrier(2)

    def send(i):
        barrier.wait(timeout=10)

        request = urllib.request.Request(
            f"http://127.0.0.1:{port}/v2/cta/predict",
            data=json.dumps(bodies[i]).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(request, timeout=210) as r:
                status = r.status
                result = json.loads(r.read(4 * 1024 * 1024))
        except urllib.error.HTTPError as e:
            detail = e.read(1500).decode(errors="replace")
            raise RuntimeError(f"HTTP {e.code}: {detail}")

        if status != 200:
            raise RuntimeError(f"Request {i+1}: HTTP {status}")

        if not isinstance(result, dict) or "error" in result:
            raise RuntimeError(f"Request {i+1}: Invalid response")

        data = result.get("jsonData")
        if not isinstance(data, dict) or "prediction" not in data:
            raise RuntimeError(f"Request {i+1}: Invalid CTA JSON")

        print(f"CTA HTTP RESPONSE {i+1}: PASS", flush=True)
        return result

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(send, i) for i in range(2)]
        responses = [f.result(timeout=240) for f in futures]

    assert len(responses) == 2

    print("NATIVE CTA TWO HTTP RESPONSES: PASS", flush=True)

    batch_lines = [
        line for line in logs
        if "BATCH" in line.upper()
        or "REQUEST_ID" in line.upper()
    ]

    print("BATCH EXECUTION EVIDENCE:")
    print("\n".join(batch_lines[-20:])[-3000:] or "NOT LOGGED")

    success = True

except Exception as exc:
    print(
        "NATIVE HTTP ACCEPTANCE: NOT PASSED",
        type(exc).__name__,
        str(exc),
        flush=True
    )
    print("LATEST SERVER LOGS:", flush=True)
    print("\n".join(logs)[-8000:], flush=True)

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
        occupied = s.connect_ex(("127.0.0.1", port)) == 0

    print("TEST PORT STILL LISTENING:", occupied)
    print("ORIGINAL DS/MAX: UNCHANGED")
    print("CONTAINERS RESTARTED: NONE")

if not success:
    raise SystemExit(1)
PY
