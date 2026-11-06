
cd /application1/sajjna8 && python3 - <<'PY'
import json
import subprocess
import tempfile
from pathlib import Path

base = Path("/application1/sajjna8")
model = Path("/application1/BPLAN_MAX_TEAM_HANDOFF_20261102")
stage = base / "max_shared_infra/isolated/bplan_shared_wiring_v1"
shared = base / "max_shared_infra/python"
rel = Path("artifacts/v1.113-max/maxserve_bplan_extension/bplan_native_serve_dev")

print("=== BPLAN SHARED MAX LIVE HTTP VALIDATION ===", flush=True)

required = [
    model / rel / "bplan_native_launcher.py",
    stage / "bplan_native_launcher.py",
    stage / "bplan_spawn_worker.py",
    stage / "bplan_router.py",
    shared / "max_runtime_shared/worker_lifecycle.py",
]
for path in required:
    if not path.is_file():
        raise SystemExit(f"STOP: Required file missing: {path}")

checks = {
    "WORKER": ("bplan_spawn_worker.py", "WorkerLifecycle("),
    "SCHEDULER": ("bplan_spawn_worker.py", "SharedSchedulerRegistry"),
    "ROUTER": ("bplan_router.py", "register_model_routes("),
}
for label, (name, marker) in checks.items():
    if marker not in (stage / name).read_text():
        raise SystemExit(f"STOP: Shared {label} wiring missing")

fixtures = [
    model / "artifacts/v1.113/core-artifact/test_samples/test_sample_1.json",
    base / "rt-pzai-bplan-v1/artifacts/v1.113/core-artifact/test_samples/test_sample_1.json",
    Path("/vzwhome/sajjna8/bplan_test_sample_for_postman.json"),
]

fixture = next((p for p in fixtures if p.is_file()), None)
if fixture is None:
    raise SystemExit("STOP: Previously verified BPLAN input not found")

payload = json.loads(fixture.read_text())
if not isinstance(payload, dict):
    raise SystemExit("STOP: Original request is not a JSON object")

print("SHARED BPLAN WIRING: VERIFIED", flush=True)
print("ORIGINAL REQUEST:", fixture, flush=True)

test = r'''
import json
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

print("SHARED MAX BPLAN SERVER: STARTING", flush=True)

logpath = Path("/tmp/bplan_shared_http.log")
log = logpath.open("w")

server = subprocess.Popen(
    [
        sys.executable, "-u", "-m",
        "bplan_native_serve_dev.bplan_native_launcher"
    ],
    stdout=log,
    stderr=subprocess.STDOUT,
)

try:
    ready = False
    for attempt in range(180):
        if server.poll() is not None:
            break
        try:
            with socket.create_connection(
                ("127.0.0.1", 18768), timeout=1
            ):
                ready = True
                break
        except OSError:
            time.sleep(1)

    if not ready:
        raise RuntimeError(
            f"BPLAN startup failed; exit={server.poll()}"
        )

    print("SHARED MAX SERVER: READY", flush=True)

    body = Path("/tmp/bplan_input.json").read_bytes()
    request = urllib.request.Request(
        "http://127.0.0.1:18768/bplan/predict",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request, timeout=240
        ) as response:
            status = response.status
            result = json.loads(response.read())
    except urllib.error.HTTPError as error:
        detail = error.read().decode(errors="replace")
        raise RuntimeError(
            f"HTTP {error.code}: {detail[:900]}"
        )

    print("HTTP STATUS:", status, flush=True)

    if status != 200:
        raise RuntimeError("BPLAN did not return HTTP 200")

    data = result.get("jsonData", result)
    if isinstance(data, dict):
        data = data.get("prediction", data)

    ctas = data.get("ctaList") if isinstance(data, dict) else None

    if not isinstance(ctas, list):
        raise RuntimeError(
            "HTTP 200 received but ctaList is missing"
        )

    print("CTA LIST COUNT:", len(ctas), flush=True)

    if len(ctas) != 4:
        raise RuntimeError(
            "Original BPLAN expected four recommendations"
        )

    print("BPLAN SHARED MAX HTTP: PASS", flush=True)
    print("SHARED BPLAN END-TO-END: PASS", flush=True)

except Exception as exc:
    print("BPLAN SHARED MAX HTTP: BLOCKED", flush=True)
    print("ERROR:", str(exc), flush=True)
    log.flush()
    lines = logpath.read_text(errors="replace").splitlines()
    print("=== SERVER ERROR DETAILS ===", flush=True)
    print("\n".join(lines[-65:]), flush=True)
    sys.exit(1)

finally:
    if server.poll() is None:
        server.terminate()
        try:
            server.wait(timeout=8)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait()
    log.close()
'''

pythonpath = ":".join([
    "/shared_infra/python",
    "/workspace/artifacts/v1.113-max/maxserve_bplan_extension",
    "/workspace/artifacts/v1.113-max/maxserve_bplan_extension/bplan_native_serve_dev",
    "/workspace/artifacts/v1.113-max",
    "/workspace/artifacts/v1.113/core-artifact",
    "/workspace/artifacts/v1.113/utils/dependency-utils",
    "/shared_deps",
])

with tempfile.TemporaryDirectory(prefix="bplan_shared_http_") as tmp:
    request_file = Path(tmp) / "bplan_input.json"
    request_file.write_text(json.dumps(payload))
    request_file.chmod(0o644)

    command = [
        "podman",
        "--root", "/application1/podman/storage",
        "--runroot", "/run/containers/storage",
        "run", "--rm", "--pull=never",
        "--network=none",
        "--memory=12g",
        "--pids-limit=512",
        "-v", f"{model}:/workspace:ro",
        "-v", f"{stage}:/workspace/{rel}:ro",
        "-v", f"{shared}:/shared_infra/python:ro",
        "-v", f"{request_file}:/tmp/bplan_input.json:ro",
        "-w", "/workspace",
        "-e", f"PYTHONPATH={pythonpath}",
    ]

    deps = Path("/application1/max_shared_python_deps")
    if deps.is_dir():
        command.extend([
            "-v", f"{deps}:/shared_deps:ro"
        ])

    command.extend([
        "--entrypoint", "/opt/venv/bin/python",
        "localhost/max-shared-runtime:cpu",
        "-u", "-c", test,
    ])

    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=480,
        )
    except subprocess.TimeoutExpired:
        raise SystemExit("STOP: BPLAN live test timed out")

    print(result.stdout[-16000:], flush=True)

    if result.returncode != 0:
        raise SystemExit(
            "STOP: BPLAN shared live HTTP not yet passing"
        )

print("=== FINAL RESULT ===")
print("BPLAN SHARED MAX HTTP: PASS")
print("ORIGINAL BPLAN HANDOFF: UNCHANGED")
print("CTA / PZAAS: UNCHANGED")
print("TEMPORARY INPUT: CLEANED")
print("NEXT: CTA SHARED MAX ADOPTION")
PY
