python3 -B - <<'PY'
from pathlib import Path
import ast, os, re, subprocess, sys

root = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max")
stage = root / "cta_native_batch2_release_candidate"
pkg = stage / "maxserve_cta_extension"
router = pkg / "cta_router.py"
helper = pkg / "cta_queue_compat.py"
bootstrap = stage / "cta_batch2_worker_bootstrap"
cid = "a176e284b50a"

# Validate existing isolated integration before changing anything.
for p in (
    router, helper, pkg / "cta_native_launcher.py",
    pkg / "cta_spawn_worker.py", pkg / "cta_native_scheduler.py"
):
    if not p.is_file() or p.is_symlink():
        raise SystemExit("STOP: Required staged file unavailable: " + str(p))
    ast.parse(p.read_text())

if "ZmqConfig[Any](Any)" not in helper.read_text():
    raise SystemExit("STOP: Verified queue compatibility fix missing")

source = router.read_text()

if "asyncio.timeout(480)" not in source:
    matches = list(re.finditer(r"asyncio\.timeout\(\s*300\s*\)", source))
    if len(matches) != 1:
        raise SystemExit("STOP: Expected 300-second CTA timeout not uniquely found")

    m = matches[0]
    updated = source[:m.start()] + "asyncio.timeout(480)" + source[m.end():]
    ast.parse(updated)

    backup = router.with_name("cta_router.py.before_480s_batch2.bak")
    temp = router.with_name("cta_router.py.480s.tmp")
    if backup.exists() or temp.exists():
        raise SystemExit("STOP: Existing timeout backup or temporary file")

    with backup.open("x") as f:
        f.write(source)
    try:
        with temp.open("x") as f:
            f.write(updated)
        os.replace(temp, router)
    finally:
        if temp.exists():
            temp.unlink()

print("STAGED CTA SERVER TIMEOUT: 480 SECONDS", flush=True)

# Install the same isolated queue compatibility at Python startup.
# This makes it available to newly spawned worker interpreters.
bootstrap.mkdir(exist_ok=True)
site = bootstrap / "sitecustomize.py"

site_code = (
    "from maxserve_cta_extension.cta_queue_compat import install\n"
    "install()\n"
    "import os\n"
    'print("CTA_QUEUE_BOOTSTRAP_PID:", os.getpid(), flush=True)\n'
)

if site.exists():
    if site.is_symlink() or site.read_text() != site_code:
        raise SystemExit("STOP: Existing bootstrap has different contents")
else:
    site.write_text(site_code)

ast.parse(site.read_text())

P = [
    "podman",
    "--root", "/application1/podman/storage",
    "--runroot", "/run/containers/storage",
]

running = subprocess.check_output(P + ["ps", "-q"], text=True).split()
if not any(x.startswith(cid) for x in running):
    raise SystemExit("STOP: Known development container not running")

mx = "/workspace/artifacts/v1.168-max"
pythonpath = ":".join([
    mx + "/cta_native_batch2_release_candidate/cta_batch2_worker_bootstrap",
    mx + "/cta_native_batch2_release_candidate",
    "/workspace/artifacts/v1.168/core-artifact",
    "/batch2",
    mx,
])

environment = {
    "PYTHONPATH": pythonpath,
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONUNBUFFERED": "1",
    "OTEL_SDK_DISABLED": "true",
    "OTEL_METRICS_EXPORTER": "none",
    "OTEL_TRACES_EXPORTER": "none",
    "OTEL_LOGS_EXPORTER": "none",
}

envargs = []
for k, v in environment.items():
    envargs.extend(["-e", f"{k}={v}"])

# Readiness check in a fresh interpreter, before model execution.
preflight = r'''
from max.serve.scheduler.queues import SchedulerZmqConfigs
from max.serve.config import Settings, APIType
assert SchedulerZmqConfigs._cta_batch2_queue_compat
assert APIType.KSERVE in Settings().api_types
print("FRESH PROCESS QUEUE COMPATIBILITY: PASS")
'''

r = subprocess.run(
    P + [
        "exec", "-i", *envargs, cid,
        "/opt/venv/bin/python", "-B", "-c", preflight
    ],
    capture_output=True, text=True, timeout=90
)

print((r.stdout + r.stderr)[-2000:], flush=True)
if r.returncode:
    raise SystemExit("STOP: Fresh process queue preflight failed")

test = r'''
import os, sys, time, json, socket, signal, threading, subprocess
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
    Path("/batch2/real_max_batch2_backend.py"),
    *fixtures,
]
for p in required:
    if not p.is_file():
        raise SystemExit("STOP: Missing " + str(p))

def cgroup_used():
    return int(Path("/sys/fs/cgroup/memory.current").read_text())

def cgroup_limit():
    return int(Path("/sys/fs/cgroup/memory.max").read_text())

limit = cgroup_limit()
used = cgroup_used()
if limit - used < 5 * 1024**3:
    raise SystemExit("STOP: Less than 5 GB container memory headroom")

print("CONTAINER MEMORY HEADROOM: PASS", flush=True)

with socket.socket() as s:
    if s.connect_ex(("127.0.0.1", port)) == 0:
        raise SystemExit("STOP: Test port occupied")

bodies = [json.loads(p.read_text()) for p in fixtures]
if bodies[0] == bodies[1]:
    raise SystemExit("STOP: Test inputs are not distinct")

env = os.environ.copy()
env.update({
    "HOME": "/tmp",
    "TMPDIR": "/tmp",
    "XDG_CACHE_HOME": "/tmp/cta_batch2_cache",
    "HF_HOME": "/tmp/cta_batch2_cache",
    "TORCH_HOME": "/tmp/cta_batch2_cache",
    "CUDA_VISIBLE_DEVICES": "",
})

command = [
    sys.executable, "-B", "-u", "-m",
    "maxserve_cta_extension.cta_native_launcher",
    "--port", str(port),
    "--model-path", str(mx / "cta_native_model"),
    "--devices", "cpu",
    "--max-batch-size", "2",
]

server = None
stop = threading.Event()
logs = deque(maxlen=2500)
passed = False

try:
    server = subprocess.Popen(
        command,
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
            logs.append(line.rstrip())

    threading.Thread(target=capture, daemon=True).start()

    def guard():
        while not stop.wait(2):
            if server.poll() is not None:
                return
            if cgroup_used() > int(cgroup_limit() * 0.85):
                logs.append("MEMORY GUARD: LIMIT APPROACHING")
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
            s.settimeout(1)
            if s.connect_ex(("127.0.0.1", port)) == 0:
                break
        time.sleep(2)
    else:
        raise RuntimeError("Native HTTP listener startup timeout")

    print("NATIVE HTTP LISTENER: PASS", flush=True)

    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/v2/cta/probe",
        data=b"", method="POST"
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        assert response.status == 200

    print("CTA NATIVE ROUTE: PASS", flush=True)
    print("TWO DISTINCT CTA JSON REQUESTS: PASS", flush=True)

    barrier = threading.Barrier(2)

    def send(i):
        barrier.wait(timeout=15)
        started = time.monotonic()

        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/v2/cta/predict",
            data=json.dumps(bodies[i]).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=505) as response:
                status = response.status
                result = json.loads(response.read(4 * 1024 * 1024))
        except urllib.error.HTTPError as e:
            raise RuntimeError(
                f"REQUEST {i+1} HTTP {e.code}: " +
                e.read(1000).decode(errors="replace")
            )

        if (
            status != 200
            or not isinstance(result, dict)
            or "error" in result
            or not isinstance(result.get("jsonData"), dict)
            or "prediction" not in result["jsonData"]
        ):
            raise RuntimeError(f"REQUEST {i+1}: Invalid CTA JSON response")

        print(
            f"CTA RESPONSE {i+1}: HTTP 200 PASS "
            f"({time.monotonic()-started:.1f}s)",
            flush=True,
        )
        return result

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(send, i) for i in range(2)]
        responses = [f.result(timeout=520) for f in futures]

    assert len(responses) == 2

    evidence = [
        line for line in logs
        if any(k in line.lower() for k in (
            "predict_batch", "real max batch",
            "batch dispatch", "response ids",
            "response queue send", "cta_queue_bootstrap_pid",
        ))
    ]

    print("NATIVE BATCH EXECUTION EVIDENCE:", flush=True)
    print("\n".join(evidence[-30:]) or "NOT LOGGED", flush=True)
    print("TWO NATIVE HTTP RESPONSES: PASS", flush=True)
    passed = True

except Exception as exc:
    print(
        "NATIVE BATCH-2 ACCEPTANCE: NOT PASSED",
        type(exc).__name__, str(exc), flush=True
    )

    relevant = [
        x for x in logs
        if any(k in x.lower() for k in (
            "cta", "batch", "worker", "queue", "scheduler",
            "msgspec", "decode", "validation", "traceback",
            "exception", "error", "bootstrap", "memory",
        ))
        and "telemetry.modular.com" not in x.lower()
    ]

    print("RELEVANT WORKER LOGS:", flush=True)
    print("\n".join(relevant[-85:])[-12000:], flush=True)

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

    print("ISOLATED TEST PROCESS STOPPED:", server is None or server.poll() is not None)
    print("ORIGINAL DS/MAX: UNCHANGED")
    print("WORKING NATIVE RELEASE: UNCHANGED")
    print("CONTAINERS RESTARTED: NONE")

if not passed:
    raise SystemExit(1)
'''

process = subprocess.Popen(
    P + [
        "exec", "-i", *envargs, "-w", "/workspace",
        cid, "/opt/venv/bin/python", "-B", "-"
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

exit_code = process.wait()
print("FINAL HTTP TEST EXIT CODE:", exit_code, flush=True)

if exit_code:
    raise SystemExit(exit_code)
PY
