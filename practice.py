
cd /application1/sajjna8 && python3 - <<'PY'
import subprocess
from pathlib import Path

base = Path("/application1/sajjna8")
model = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030")
rel = Path("artifacts/v1.168-max/cta_native_batch2_release_candidate/maxserve_cta_extension")
stage = base / "max_shared_infra/isolated/cta_shared_wiring_v1"
shared = base / "max_shared_infra/python"
fixture = base / "rt-pzaas-cta-offers-v1/artifacts/v1.168-max/cta_native_adjusted_sanity_input.json"

print("=== CTA SHARED MAX CORRECTED LIVE HTTP ===", flush=True)

required = [
    model / "artifacts/v1.168-max/cta_native_model",
    stage / "cta_native_launcher.py",
    stage / "cta_spawn_worker.py",
    stage / "cta_router.py",
    stage / "cta_queue_compat.py",
    shared / "max_runtime_shared/worker_lifecycle.py",
    fixture,
]
for path in required:
    if not path.exists():
        raise SystemExit(f"STOP: Missing required path: {path}")

import json
if not isinstance(json.loads(fixture.read_text()), dict):
    raise SystemExit("STOP: Invalid original CTA request")

inside = r'''
import json
import socket
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

logpath = Path("/tmp/cta_shared_verified.log")
port = 18767

startup = [
    sys.executable, "-B", "-u", "-c",
    "from maxserve_cta_extension.cta_queue_compat import install; "
    "assert install(); "
    "from maxserve_cta_extension.cta_native_launcher import main; "
    "main()",
    "--port", str(port),
    "--model-path",
    "/workspace/artifacts/v1.168-max/cta_native_model",
    "--devices", "cpu",
    "--max-batch-size", "2",
]

print("CTA STARTUP: ORIGINAL VERIFIED ARGUMENTS", flush=True)
server = None
passed = False

try:
    with logpath.open("w") as log:
        server = subprocess.Popen(
            startup,
            stdout=log,
            stderr=subprocess.STDOUT
        )

        ready = False

        for _ in range(240):
            if server.poll() is not None:
                break
            try:
                with socket.create_connection(
                    ("127.0.0.1", port), timeout=1
                ):
                    ready = True
                    break
            except OSError:
                time.sleep(1)

        if not ready:
            raise RuntimeError("CTA server did not become ready")

        print("CTA SHARED SERVER: READY", flush=True)

        body = Path("/tmp/cta_input.json").read_bytes()

        for route in ("/cta/predict", "/cta/infer"):
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}{route}",
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            try:
                with urllib.request.urlopen(
                    req, timeout=240
                ) as response:
                    status = response.status
                    result = json.loads(response.read())

                if status != 200:
                    raise RuntimeError(f"HTTP {status}")

                if not isinstance(result, (dict, list)) or not result:
                    raise RuntimeError("Invalid or empty JSON")

                if isinstance(result, dict) and (
                    "error" in result or "detail" in result
                ):
                    raise RuntimeError(str(result)[:500])

                print("CTA ENDPOINT:", route, flush=True)
                print("HTTP STATUS:", status, flush=True)
                print("REAL CTA JSON: PASS", flush=True)
                passed = True
                break

            except urllib.error.HTTPError as exc:
                detail = exc.read().decode(errors="replace")
                if exc.code == 404:
                    continue
                raise RuntimeError(
                    f"{route}: HTTP {exc.code}: {detail[:600]}"
                )

        if not passed:
            raise RuntimeError("No CTA route returned valid HTTP 200")

        print("CTA SHARED MAX HTTP: PASS", flush=True)

except Exception as exc:
    print("CTA SHARED MAX HTTP: BLOCKED", flush=True)
    print("ERROR:", exc, flush=True)
    if logpath.exists():
        print("=== LAST SERVER LOG LINES ===", flush=True)
        print("\n".join(
            logpath.read_text(errors="replace").splitlines()[-45:]
        ), flush=True)
    sys.exit(1)

finally:
    if server is not None and server.poll() is None:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait()
'''

pythonpath = ":".join([
    "/shared_infra/python",
    "/workspace/artifacts/v1.168-max/cta_native_batch2_release_candidate",
    "/workspace/artifacts/v1.168-max/cta_native_batch2_release_candidate/maxserve_cta_extension",
    "/workspace/artifacts/v1.168-max",
    "/workspace/artifacts/v1.168/core-artifact",
    "/workspace/artifacts/v1.168/utils/dependency-utils",
    "/workspace",
    "/shared_deps/sklearn161",
    "/shared_deps",
])

cmd = [
    "podman",
    "--root", "/application1/podman/storage",
    "--runroot", "/run/containers/storage",
    "run", "--rm", "--pull=never",
    "--network=none",
    "--memory=18g",
    "--pids-limit=512",
    "-v", f"{model}:/workspace:ro",
    "-v", f"{stage}:/workspace/{rel}:ro",
    "-v", f"{shared}:/shared_infra/python:ro",
    "-v", f"{fixture}:/tmp/cta_input.json:ro",
    "-w", "/workspace",
    "-e", f"PYTHONPATH={pythonpath}",
]

deps = Path("/application1/max_shared_python_deps")
if deps.is_dir():
    cmd.extend(["-v", f"{deps}:/shared_deps:ro"])

cmd.extend([
    "--entrypoint", "/opt/venv/bin/python",
    "localhost/max-shared-runtime:cpu",
    "-u", "-c", inside
])

try:
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=540
    )
except subprocess.TimeoutExpired:
    raise SystemExit("STOP: CTA shared HTTP verification timed out")

print(result.stdout[-14000:], flush=True)

if result.returncode != 0:
    raise SystemExit("STOP: CTA shared HTTP not yet verified")

print("\n=== RESULT ===")
print("CTA SHARED MAX HTTP: PASS")
print("ORIGINAL MODEL CODE: UNCHANGED")
print("CTA / BPLAN / PZAAS HANDOFFS: UNCHANGED")
print("NEXT: SIMULTANEOUS THREE-MODEL VALIDATION")
PY
