python3 -B - <<'PY'
from pathlib import Path
import ast, os, re, subprocess

root = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max")
stage = root / "cta_native_batch2_release_candidate"
pkg = stage / "maxserve_cta_extension"
router = pkg / "cta_router.py"
helper = pkg / "cta_queue_compat.py"

for p in (router, helper, pkg/"cta_native_launcher.py", pkg/"cta_spawn_worker.py"):
    if not p.is_file() or p.is_symlink():
        raise SystemExit("STOP: Missing isolated source: " + str(p))
    ast.parse(p.read_text())

if "ZmqConfig[Any](Any)" not in helper.read_text():
    raise SystemExit("STOP: Previously verified queue fix missing")

# Change only the staged router. Never change the working release.
source = router.read_text()
if "asyncio.timeout(480)" not in source:
    matches = list(re.finditer(r"asyncio\.timeout\(\s*300\s*\)", source))
    if len(matches) != 1:
        raise SystemExit("STOP: Expected staged 300s timeout not uniquely found")

    m = matches[0]
    updated = source[:m.start()] + "asyncio.timeout(480)" + source[m.end():]
    ast.parse(updated)

    backup = router.with_name("cta_router.py.before_480s_batch2.bak")
    temp = router.with_name("cta_router.py.480s.tmp")
    if backup.exists() or temp.exists():
        raise SystemExit("STOP: Existing backup or temp file")

    with backup.open("x") as f:
        f.write(source)
    try:
        with temp.open("x") as f:
            f.write(updated)
        os.replace(temp, router)
    finally:
        if temp.exists():
            temp.unlink()

print("STAGED SERVER TIMEOUT: 480 SECONDS", flush=True)

# Apply the verified queue compatibility fix at Python startup,
# including newly spawned worker interpreters.
bootdir = stage / "cta_batch2_worker_bootstrap"
if bootdir.is_symlink():
    raise SystemExit("STOP: Unexpected bootstrap symlink")
bootdir.mkdir(exist_ok=True)
boot = bootdir / "sitecustomize.py"

boot_code = '''from maxserve_cta_extension.cta_queue_compat import install
install()
import os
print("CTA_QUEUE_BOOTSTRAP_PID:", os.getpid(), flush=True)
'''

if boot.exists():
    if boot.is_symlink() or boot.read_text() != boot_code:
        raise SystemExit("STOP: Existing bootstrap differs")
else:
    with boot.open("x") as f:
        f.write(boot_code)

ast.parse(boot.read_text())

P = [
    "podman",
    "--root", "/application1/podman/storage",
    "--runroot", "/run/containers/storage",
]
cid = "a176e284b50a"

ids = subprocess.check_output(P + ["ps", "-q"], text=True).split()
if not any(x.startswith(cid) for x in ids):
    raise SystemExit("STOP: Existing development container unavailable")

mx = "/workspace/artifacts/v1.168-max"
pythonpath = ":".join([
    mx + "/cta_native_batch2_release_candidate/cta_batch2_worker_bootstrap",
    mx + "/cta_native_batch2_release_candidate",
    "/workspace/artifacts/v1.168/core-artifact",
    "/batch2",
    mx,
])

envargs = []
for k, v in {
    "PYTHONPATH": pythonpath,
    "PYTHONDONTWRITEBYTECODE": "1",
    "OTEL_SDK_DISABLED": "true",
    "OTEL_METRICS_EXPORTER": "none",
    "OTEL_TRACES_EXPORTER": "none",
    "OTEL_LOGS_EXPORTER": "none",
}.items():
    envargs += ["-e", f"{k}={v}"]

# Fresh-interpreter verification, not just launcher import.
check = '''
from max.serve.scheduler.queues import SchedulerZmqConfigs
from max.serve.config import Settings, APIType
assert SchedulerZmqConfigs._cta_batch2_queue_compat
assert APIType.KSERVE in Settings().api_types
print("FRESH WORKER QUEUE PREFLIGHT: PASS")
'''

r = subprocess.run(
    P + ["exec", "-i", *envargs, cid,
         "/opt/venv/bin/python", "-B", "-c", check],
    capture_output=True, text=True, timeout=90
)
print((r.stdout + r.stderr)[-1500:], flush=True)
if r.returncode:
    raise SystemExit("STOP: Fresh-process preflight failed; no inference launched")

# One isolated native HTTP acceptance attempt.
inside = r'''
import os, sys, time, signal, socket, json, threading, collections, subprocess
import urllib.request, urllib.error
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

mx = Path("/workspace/artifacts/v1.168-max")
stage = mx / "cta_native_batch2_release_candidate"
port = 18767
fixtures = [
    mx / "test-results/cta_max_tiles_smoketest_input.json",
    mx / "cta_native_adjusted_sanity_input.json",
]

for p in [
    stage / "maxserve_cta_extension/cta_native_launcher.py",
    mx / "cta_native_model/config.json",
    Path("/batch2/real_max_batch2_backend.py"),
    *fixtures,
]:
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

with socket.socket() as s:
    if s.connect_ex(("127.0.0.1", port)) == 0:
        raise SystemExit("STOP: Isolated port occupied")

env = os.environ.copy()
env.update({
    "PYTHONUNBUFFERED": "1",
    "HOME": "/tmp",
    "TMPDIR": "/tmp",
    "XDG_CACHE_HOME": "/tmp/cta_batch2_cache",
    "HF_HOME": "/tmp/cta_batch2_cache",
    "TORCH_HOME": "/tmp/cta_batch2_cache",
    "CUDA_VISIBLE_DEVICES": "",
})

logs = collections.deque(maxlen=700)
stop = threading.Event()
server = None
success = False

try:
    server = subprocess.Popen(
        [
            sys.executable, "-B", "-u", "-m",
            "maxserve_cta_extension.cta_native_launcher",
            "--port", str(port),
            "--model-path", str(mx / "cta_native_model"),
            "--devices", "cpu",
            "--max-batch-size", "2",
        ],
        cwd="/workspace",
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        start_new_session=True,
    )

    def collect():
        for line in server.stdout:
            line = line.rstrip()
            if any(s in line for s in (
                "telemetry.modular.com",
                "NameResolutionError",
                "MaxRetryError",
            )):
                continue
            logs.append(line)

    threading.Thread(target=collect, daemon=True).start()

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

    threading.Thread(target=memory_guard, daemon=True).start()

    print("NATIVE BATCH-2 HTTP TEST: START", flush=True)

    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        if server.poll() is not None:
            raise RuntimeError("Native server exited during startup")
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", port)) == 0:
                break
        time.sleep(2)
    else:
        raise RuntimeError("Native listener startup timeout")

    print("NATIVE HTTP LISTENER: PASS", flush=True)

    probe = urllib.request.Request(
        f"http://127.0.0.1:{port}/v2/cta/probe",
        data=b"",
        method="POST",
    )
    with urllib.request.urlopen(probe, timeout=20) as response:
        assert response.status == 200

    print("CTA HTTP ROUTE: PASS", flush=True)

    bodies = [json.loads(p.read_text()) for p in fixtures]
    assert bodies[0] != bodies[1]
    print("DISTINCT JSON REQUESTS: PASS", flush=True)

    barrier = threading.Barrier(2)

    def send(i):
        barrier.wait(timeout=15)
        request = urllib.request.Request(
            f"http://127.0.0.1:{port}/v2/cta/predict",
            data=json.dumps(bodies[i]).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=505) as response:
                status = response.status
                result = json.loads(response.read(4 * 1024 * 1024))
        except urllib.error.HTTPError as e:
            raise RuntimeError(
                f"HTTP {e.code}: " +
                e.read(700).decode(errors="replace")
            )

        if (
            status != 200
            or not isinstance(result, dict)
            or "error" in result
            or not isinstance(result.get("jsonData"), dict)
            or "prediction" not in result["jsonData"]
        ):
            raise RuntimeError(f"Invalid CTA response {i+1}")

        print(f"CTA HTTP RESPONSE {i+1}: PASS", flush=True)
        return result

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(send, i) for i in range(2)]
        results = [f.result(timeout=520) for f in futures]

    assert len(results) == 2
    print("NATIVE TWO-REQUEST HTTP ACCEPTANCE: PASS", flush=True)

    evidence = [
        x for x in logs
        if any(k in x.lower() for k in (
            "predict_batch",
            "real max batch",
            "batch dispatch",
            "response ids",
            "response queue send",
        ))
    ]
    print(
        "ONE-BATCH / REQUEST-ID EVIDENCE:",
        " | ".join(evidence[-15:]) or "NOT LOGGED",
        flush=True,
    )
    success = True

except Exception as exc:
    print(
        "NATIVE ACCEPTANCE: NOT PASSED",
        type(exc).__name__, str(exc),
        flush=True,
    )
    relevant = [
        x for x in logs
        if any(k in x.lower() for k in (
            "cta", "batch", "worker", "queue",
            "scheduler", "msgspec", "validation",
            "exception", "error", "bootstrap", "traceback",
        ))
    ]
    print("RELEVANT WORKER LOGS:")
    print("\n".join(relevant[-65:])[-9500:], flush=True)

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
    print("CONTAINERS RESTARTED: NONE")

if not success:
    raise SystemExit(1)
'''

r = subprocess.run(
    P + [
        "exec", "-i", *envargs,
        "-w", "/workspace", cid,
        "/opt/venv/bin/python", "-B", "-",
    ],
    input=inside,
    text=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    timeout=800,
)

print(r.stdout[-11500:], flush=True)
print("FINAL HTTP TEST EXIT CODE:", r.returncode, flush=True)

if r.returncode:
    raise SystemExit(r.returncode)
PY
