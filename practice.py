python3 -B - <<'PY'
from pathlib import Path
import ast
import tarfile
import subprocess
import os

repo = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1")
mx = repo / "artifacts/v1.168-max"
pkg = mx / "cta_native_batch2_release_candidate/maxserve_cta_extension"
target = pkg / "cta_native_launcher_proven_queue.py"

required = (
    "cta_native_launcher.py",
    "cta_native_scheduler.py",
    "cta_worker_adapter.py",
    "cta_router.py",
)

if not all((pkg / name).is_file() for name in required):
    raise SystemExit("STOP: Staged native Batch-2 package missing")

def verified(source):
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False

    hooked = any(
        isinstance(node, ast.Assign)
        and any(
            isinstance(t, ast.Attribute)
            and t.attr == "__init__"
            and isinstance(t.value, ast.Name)
            and t.value.id == "SchedulerZmqConfigs"
            for t in node.targets
        )
        for node in ast.walk(tree)
    )

    return hooked and all(
        item in source for item in (
            "SchedulerZmqConfigs",
            "ZmqConfig[Any]",
            "register_cta_routes",
            "max.entrypoints.pipelines",
        )
    )

sources = [
    Path(
        "/application1/cta_max_native_release_candidate_20261028/"
        "cta_native_launcher.py"
    ),
    Path(
        "/application1/cta_max_native_release_candidate_20261028/"
        "maxserve_cta_extension/cta_native_launcher.py"
    ),
    mx / "maxserve_cta_extension/cta_native_launcher.py",
]

chosen = None

for path in sources:
    if path.is_file() and not path.is_symlink():
        source = path.read_text()
        if verified(source):
            chosen = (str(path), source)
            break

if chosen is None:
    archives = [
        Path("/application1/CTA_MAX_NATIVE_E2E_PASS_20261028.tar.gz"),
        Path("/application1/cta_max_native_http_pass_20261028.tar.gz"),
    ]

    for archive in archives:
        if not archive.is_file():
            continue

        try:
            with tarfile.open(archive, "r:gz") as tar:
                for member in tar:
                    if not member.isfile():
                        continue
                    if Path(member.name).name != "cta_native_launcher.py":
                        continue
                    if member.size > 200000:
                        continue

                    fileobj = tar.extractfile(member)
                    if fileobj is None:
                        continue

                    source = fileobj.read().decode("utf-8")

                    if verified(source):
                        chosen = (
                            str(archive) + "!" + member.name,
                            source,
                        )
                        break
        except (OSError, tarfile.TarError, UnicodeError):
            pass

        if chosen is not None:
            break

if chosen is None:
    raise SystemExit(
        "STOP: Proven October 28 queue bridge unavailable. "
        "No files changed."
    )

source_name, source = chosen

if target.exists():
    if not target.is_file() or target.read_text() != source:
        raise SystemExit(
            "STOP: Existing staged launcher differs. No overwrite."
        )
else:
    fd = os.open(
        str(target),
        os.O_WRONLY | os.O_CREAT | os.O_EXCL,
        0o644,
    )
    with os.fdopen(fd, "w") as f:
        f.write(source)

print("PROVEN QUEUE BRIDGE SOURCE:", source_name, flush=True)
print("STAGED QUEUE BRIDGE: PASS", flush=True)

P = [
    "podman",
    "--root", "/application1/podman/storage",
    "--runroot", "/run/containers/storage",
]

ids = subprocess.check_output(
    P + ["ps", "-q"], text=True
).split()

ids = [x for x in ids if x.startswith("a176e284b50a")]

if len(ids) != 1:
    raise SystemExit("STOP: Existing development container unavailable")

inside = r"""
import os, sys, time, signal, socket, json
import subprocess, threading, collections
import urllib.request, urllib.error
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

mx = Path("/workspace/artifacts/v1.168-max")
core = Path("/workspace/artifacts/v1.168/core-artifact")
stage = mx / "cta_native_batch2_release_candidate"
model = mx / "cta_native_model"
port = 18767

fixtures = [
    mx / "test-results/cta_max_tiles_smoketest_input.json",
    mx / "cta_native_adjusted_sanity_input.json",
]

required = [
    core / "pipeline.py",
    stage / "maxserve_cta_extension/cta_native_launcher_proven_queue.py",
    model / "config.json",
    Path("/batch2/real_max_batch2_backend.py"),
    *fixtures,
]

for p in required:
    if not p.is_file():
        raise SystemExit("STOP: Missing " + str(p))

def memory_mb():
    return int(next(
        x.split()[1]
        for x in Path("/proc/meminfo").read_text().splitlines()
        if x.startswith("MemAvailable:")
    )) // 1024

if memory_mb() < 12000:
    raise SystemExit("STOP: Insufficient memory")

fs = os.statvfs("/workspace")

if fs.f_bavail * fs.f_frsize < 20 * 1024**3:
    raise SystemExit("STOP: Insufficient workspace disk")

with socket.socket() as s:
    if s.connect_ex(("127.0.0.1", port)) == 0:
        raise SystemExit("STOP: Test port occupied")

env = os.environ.copy()
env.update({
    "PYTHONPATH": f"{stage}:{core}:/batch2:{mx}",
    "PYTHONDONTWRITEBYTECODE": "1",
    "HOME": "/tmp",
    "TMPDIR": "/tmp",
    "XDG_CACHE_HOME": "/tmp/cta_queuebridge_cache",
    "CUDA_VISIBLE_DEVICES": "",
})

launcher = r'''
from max.serve.config import Settings, APIType
import sys, runpy

original_init = Settings.__init__

def enable_kserve(self, *args, **kwargs):
    original_init(self, *args, **kwargs)
    if APIType.KSERVE not in self.api_types:
        self.api_types = list(self.api_types) + [APIType.KSERVE]

Settings.__init__ = enable_kserve

assert APIType.KSERVE in Settings().api_types

sys.argv = [
    "cta_native_launcher_proven_queue",
    "--port", "18767",
    "--model-path",
    "/workspace/artifacts/v1.168-max/cta_native_model",
    "--devices", "cpu",
    "--max-batch-size", "2",
]

runpy.run_module(
    "maxserve_cta_extension.cta_native_launcher_proven_queue",
    run_name="__main__",
)
'''

server = None
logs = collections.deque(maxlen=350)
stop = threading.Event()
passed = False

try:
    print("NATIVE QUEUE BRIDGE HTTP TEST: START", flush=True)

    server = subprocess.Popen(
        [sys.executable, "-B", "-u", "-c", launcher],
        env=env,
        cwd="/workspace",
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

    def memory_guard():
        while not stop.wait(2):
            if server.poll() is not None:
                return
            if memory_mb() < 5500:
                logs.append("STOP: Memory reserve too low")
                try:
                    os.killpg(server.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                return

    threading.Thread(target=memory_guard, daemon=True).start()

    deadline = time.monotonic() + 165

    while time.monotonic() < deadline:
        if server.poll() is not None:
            raise RuntimeError("Native MAX worker exited")

        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", port)) == 0:
                break

        time.sleep(2)
    else:
        raise RuntimeError("Native server startup timeout")

    print("NATIVE HTTP LISTENER: PASS", flush=True)

    probe = urllib.request.Request(
        f"http://127.0.0.1:{port}/v2/cta/probe",
        data=b"",
        method="POST",
    )

    with urllib.request.urlopen(probe, timeout=15) as response:
        assert response.status == 200

    print("NATIVE CTA HTTP ROUTE: PASS", flush=True)

    bodies = [json.loads(p.read_text()) for p in fixtures]
    barrier = threading.Barrier(2)

    def send(i):
        barrier.wait(timeout=10)

        request = urllib.request.Request(
            f"http://127.0.0.1:{port}/v2/cta/predict",
            data=json.dumps(bodies[i]).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=205) as r:
                status = r.status
                payload = json.loads(r.read(4 * 1024 * 1024))
        except urllib.error.HTTPError as e:
            detail = e.read(1000).decode(errors="replace")
            raise RuntimeError(f"HTTP {e.code}: {detail}")

        if (
            status != 200
            or not isinstance(payload, dict)
            or "error" in payload
            or not isinstance(payload.get("jsonData"), dict)
            or "prediction" not in payload["jsonData"]
        ):
            raise RuntimeError(f"Invalid CTA response {i+1}")

        print(f"CTA HTTP RESPONSE {i+1}: PASS", flush=True)
        return payload

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(send, i) for i in range(2)]
        responses = [f.result(timeout=225) for f in futures]

    assert len(responses) == 2

    print("NATIVE CTA TWO HTTP RESPONSES: PASS", flush=True)

    evidence = [
        line for line in logs
        if "BATCH" in line.upper()
        or "REQUEST_ID" in line.upper()
    ]

    print(
        "BATCH EXECUTION LOGS:",
        "\n".join(evidence[-14:])[-1800:] or "NONE",
        flush=True,
    )

    print(
        "SINGLE MAX EXECUTION / REQUEST-ID PROOF: "
        "REQUIRES RUNTIME EVIDENCE",
        flush=True,
    )

    passed = True

except Exception as exc:
    print(
        "NATIVE HTTP ACCEPTANCE: NOT PASSED",
        type(exc).__name__,
        str(exc),
        flush=True,
    )
    print("LATEST NATIVE LOGS:", flush=True)
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

    print(
        "ISOLATED TEST PROCESS STOPPED:",
        server is None or server.poll() is not None,
        flush=True,
    )
    print("ORIGINAL DS/MAX: UNCHANGED")
    print("CONTAINERS RESTARTED: NONE")

if not passed:
    raise SystemExit(1)
"""

r = subprocess.run(
    P + [
        "exec", "-i", "-w", "/workspace",
        "-e", "PYTHONDONTWRITEBYTECODE=1",
        ids[0],
        "/opt/venv/bin/python", "-B", "-",
    ],
    input=inside,
    text=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    timeout=460,
)

print(r.stdout[-9500:])
print("ACCEPTANCE EXIT CODE:", r.returncode)

if r.returncode != 0:
    raise SystemExit(r.returncode)
PY
