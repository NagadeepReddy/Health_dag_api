python3 -B - <<'PY'
from pathlib import Path
import ast, os, subprocess, tempfile, sys

P = [
    "podman",
    "--root", "/application1/podman/storage",
    "--runroot", "/run/containers/storage",
]
cid = "0c95d4a8f887"

ids = subprocess.check_output(P + ["ps", "-q"], text=True).split()
if not any(i.startswith(cid) for i in ids):
    raise SystemExit("STOP: Known 14GB Batch-2 container not running")

base = Path(
    "/application1/sajjna8/rt-pzaas-cta-offers-v1/"
    "artifacts/v1.168-max"
)
stage = base / "cta_native_batch2_release_candidate"
pkg = stage / "maxserve_cta_extension"
helper = pkg / "cta_queue_compat.py"
router = pkg / "cta_router.py"

marker = "CTA_BATCH2_TYPED_RESPONSE_QUEUE_V2"

for p in (
    helper,
    router,
    pkg / "cta_native_launcher.py",
    pkg / "cta_native_scheduler.py",
):
    if not p.is_file() or p.is_symlink():
        raise SystemExit("STOP: Missing isolated file: " + str(p))
    ast.parse(p.read_text())

if "asyncio.timeout(480)" not in router.read_text():
    raise SystemExit("STOP: Previously staged timeout not found")

source = helper.read_text()

if marker not in source:
    if (
        source.count("def install(") != 1
        or "ZmqConfig[Any](Any)" not in source
    ):
        raise SystemExit("STOP: Existing queue helper differs")

    patch = '''
# CTA_BATCH2_TYPED_RESPONSE_QUEUE_V2
_cta_existing_install = install

def install():
    status = _cta_existing_install()

    from max.serve.scheduler.queues import SchedulerZmqConfigs
    from max.serve.queue.zmq_queue import ZmqConfig
    from max.interfaces.request import RequestID
    from max.interfaces.scheduler import SchedulerResult
    from maxserve_cta_extension.cta_native_scheduler import CTASerializableOutput

    response_type = dict[
        RequestID,
        SchedulerResult[CTASerializableOutput]
    ]

    prior_init = SchedulerZmqConfigs.__init__

    if not getattr(prior_init, "_cta_batch2_typed_response_v2", False):
        def cta_typed_response_init(self, pipeline_task):
            prior_init(self, pipeline_task)
            self.response_queue_config = ZmqConfig[response_type](
                response_type
            )

        cta_typed_response_init._cta_batch2_typed_response_v2 = True
        SchedulerZmqConfigs.__init__ = cta_typed_response_init

    return status
'''

    updated = source.rstrip() + "\n\n" + patch
    ast.parse(updated)
    compile(updated, str(helper), "exec")

    backup = pkg / "cta_queue_compat.py.before_typed_response_v2.bak"

    if backup.exists() or backup.is_symlink():
        raise SystemExit("STOP: Existing backup; refusing overwrite")

    with backup.open("x") as f:
        f.write(source)

    fd, tmp = tempfile.mkstemp(
        prefix=".cta_queue_compat_",
        suffix=".tmp",
        dir=pkg,
    )

    try:
        with os.fdopen(fd, "w") as f:
            f.write(updated)
        os.replace(tmp, helper)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

print("ISOLATED RESPONSE QUEUE PATCH: INSTALLED", flush=True)

mx = "/workspace/artifacts/v1.168-max"

pythonpath = ":".join([
    mx + "/cta_native_batch2_release_candidate",
    "/workspace/artifacts/v1.168/core-artifact",
    "/batch2",
    mx,
])

envargs = []

for k, v in {
    "PYTHONPATH": pythonpath,
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONUNBUFFERED": "1",
    "OTEL_SDK_DISABLED": "true",
    "OTEL_METRICS_EXPORTER": "none",
    "OTEL_TRACES_EXPORTER": "none",
    "OTEL_LOGS_EXPORTER": "none",
}.items():
    envargs += ["-e", f"{k}={v}"]

# Verify the exact response encoding/decoding contract
# before executing any model.
preflight = '''
from maxserve_cta_extension.cta_queue_compat import install
from max.serve.scheduler.queues import SchedulerZmqConfigs

assert install()
assert getattr(
    SchedulerZmqConfigs.__init__,
    "_cta_batch2_typed_response_v2",
    False
)

from max.interfaces.request import RequestID
from max.interfaces.scheduler import SchedulerResult
from maxserve_cta_extension.cta_native_scheduler import CTASerializableOutput
from max.serve.queue.zmq_queue import ZmqConfig
import msgspec

T = dict[RequestID, SchedulerResult[CTASerializableOutput]]

config = ZmqConfig[T](T)
msgspec.msgpack.Decoder(type=T)

mock = {
    RequestID("cta-codec-check"): SchedulerResult.create(
        CTASerializableOutput(
            is_done=True,
            result={"prediction": []}
        )
    )
}

packed = msgspec.msgpack.encode(mock)
restored = msgspec.msgpack.decode(packed, type=T)

assert len(restored) == 1

print("CTA RESPONSE SERIALIZATION ROUNDTRIP: PASS", flush=True)
'''

try:
    r = subprocess.run(
        P + [
            "exec", "-i", *envargs, cid,
            "/opt/venv/bin/python", "-B", "-u", "-c", preflight
        ],
        capture_output=True,
        text=True,
        timeout=100,
    )
except subprocess.TimeoutExpired:
    raise SystemExit(
        "STOP: Response codec import timed out. "
        "No native inference started."
    )

print((r.stdout + r.stderr)[-2500:], flush=True)

if r.returncode:
    raise SystemExit(
        "STOP: Response codec verification failed. "
        "No native inference started."
    )

# Run one actual two-request native MAX Serve HTTP acceptance.
test = r'''
import os, sys, time, json, signal, socket, subprocess, threading
import urllib.request, urllib.error
from pathlib import Path
from collections import deque
from concurrent.futures import ThreadPoolExecutor

mx = Path("/workspace/artifacts/v1.168-max")

fixtures = [
    mx / "test-results/cta_max_tiles_smoketest_input.json",
    mx / "cta_native_adjusted_sanity_input.json",
]

required = [
    mx / "cta_native_model/config.json",
    Path("/batch2/real_max_batch2_backend.py"),
    *fixtures,
]

for p in required:
    if not p.is_file():
        raise SystemExit("STOP: Missing model/backend/fixture: " + str(p))

bodies = [json.loads(p.read_text()) for p in fixtures]

if bodies[0] == bodies[1]:
    raise SystemExit("STOP: Requests are not distinct")

limit_text = Path("/sys/fs/cgroup/memory.max").read_text().strip()

if not limit_text.isdigit():
    raise SystemExit("STOP: Container memory limit unavailable")

limit = int(limit_text)

def used():
    return int(Path("/sys/fs/cgroup/memory.current").read_text())

if limit - used() < 5 * 1024**3:
    raise SystemExit("STOP: Less than 5 GB memory headroom")

print("CONTAINER MEMORY SAFETY: PASS", flush=True)

port = 18767

with socket.socket() as s:
    if s.connect_ex(("127.0.0.1", port)) == 0:
        raise SystemExit("STOP: Isolated test port occupied")

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
logs = deque(maxlen=2200)
stop = threading.Event()
worker_failed = threading.Event()
passed = False

try:
    server = subprocess.Popen(
        cmd,
        cwd="/workspace",
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        start_new_session=True,
    )

    def capture():
        for line in server.stdout:
            if "telemetry.modular.com" not in line:
                logs.append(line.rstrip())

            if (
                "ValidationError" in line
                or "CTA RESPONSE WORKER LOOP: EXIT" in line
            ):
                worker_failed.set()

    threading.Thread(target=capture, daemon=True).start()

    def guard():
        while not stop.wait(1):
            if server.poll() is not None:
                return

            if worker_failed.is_set() or used() > limit * 0.85:
                logs.append(
                    "STOP: WORKER SERIALIZATION ERROR OR MEMORY GUARD"
                )
                try:
                    os.killpg(server.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                return

    threading.Thread(target=guard, daemon=True).start()

    print("NATIVE MAX BATCH-2: START", flush=True)

    deadline = time.monotonic() + 180

    while time.monotonic() < deadline:
        if server.poll() is not None:
            raise RuntimeError("Native server exited during startup")

        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", port)) == 0:
                break

        time.sleep(2)
    else:
        raise RuntimeError("Native HTTP listener unavailable")

    print("NATIVE HTTP LISTENER: PASS", flush=True)

    probe = urllib.request.Request(
        f"http://127.0.0.1:{port}/v2/cta/probe",
        data=b"",
        method="POST",
    )

    with urllib.request.urlopen(probe, timeout=20) as response:
        assert response.status == 200

    print("NATIVE CTA ROUTE: PASS", flush=True)

    barrier = threading.Barrier(2)

    def send(i):
        barrier.wait(timeout=15)

        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/v2/cta/predict",
            data=json.dumps(bodies[i]).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=245) as response:
                status = response.status
                result = json.loads(response.read(4 * 1024 * 1024))
        except urllib.error.HTTPError as e:
            raise RuntimeError(
                f"Request {i+1}: HTTP {e.code}: "
                + e.read(700).decode(errors="replace")
            )

        if (
            status != 200
            or not isinstance(result, dict)
            or not isinstance(result.get("jsonData"), dict)
            or "prediction" not in result["jsonData"]
        ):
            raise RuntimeError(f"Request {i+1}: Invalid CTA response")

        print(f"CTA NATIVE HTTP RESPONSE {i+1}: 200 PASS", flush=True)
        return result

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(send, i) for i in range(2)]
        responses = [f.result(timeout=265) for f in futures]

    assert len(responses) == 2

    print("TWO DISTINCT CTA HTTP REQUESTS: PASS", flush=True)

    evidence = [
        line for line in logs
        if any(
            term in line.upper()
            for term in (
                "CTA TRUE MAX BATCH-2",
                "REAL BATCH-2 INPUTS",
                "CTA RESPONSE WORKER",
                "RESPONSE IDS",
                "BATCH DISPATCH",
                "CTA_QUEUE",
            )
        )
    ]

    print("BATCH EXECUTION / RESPONSE LOGS:", flush=True)
    print("\n".join(evidence[-25:])[-4000:] or "NOT LOGGED")

    markers = [
        line for line in evidence
        if "CTA TRUE MAX BATCH-2: TWO JSON RESPONSES PRODUCED" in line
    ]

    if (
        len(markers) != 1
        or not any(
            "REAL BATCH-2 INPUTS: PASS 72" in line
            for line in evidence
        )
    ):
        raise RuntimeError(
            "Native single-batch execution evidence "
            "absent or repeated"
        )

    print("REAL ONE-BATCH WORKER EVIDENCE: PASS", flush=True)
    passed = True

except Exception as exc:
    print(
        "NATIVE BATCH-2 HTTP: NOT PASSED",
        type(exc).__name__,
        str(exc),
        flush=True,
    )

    relevant = [
        line for line in logs
        if any(
            term in line.lower()
            for term in (
                "cta", "batch", "worker", "queue",
                "error", "exception", "validation",
                "traceback", "memory", "request_id",
            )
        )
        and "telemetry.modular.com" not in line.lower()
    ]

    print("RELEVANT WORKER LOGS:", flush=True)
    print("\n".join(relevant[-70:])[-10500:], flush=True)

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
        "ISOLATED TEST STOPPED:",
        server is None or server.poll() is not None,
        flush=True,
    )
    print("ORIGINAL DS/MAX: UNCHANGED", flush=True)
    print("WORKING RELEASE: UNCHANGED", flush=True)
    print("CONTAINERS RESTARTED: NONE", flush=True)

if not passed:
    raise SystemExit(1)
'''

process = subprocess.Popen(
    P + [
        "exec", "-i", "-w", "/workspace",
        *envargs,
        cid,
        "/opt/venv/bin/python", "-B", "-u", "-"
    ],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1,
)

process.stdin.write(test)
process.stdin.close()

for line in process.stdout:
    print(line, end="", flush=True)

rc = process.wait()

print("NATIVE BATCH-2 FINAL EXIT CODE:", rc, flush=True)

if rc:
    sys.exit(rc)
PY
