
cd /application1/sajjna8 && python3 - <<'PY'
import json
import subprocess
from pathlib import Path

base = Path("/application1/sajjna8")
model = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030")
rel = Path("artifacts/v1.168-max/cta_native_batch2_release_candidate/maxserve_cta_extension")
stage = base / "max_shared_infra/isolated/cta_shared_wiring_v1"
shared = base / "max_shared_infra/python"
fixture = base / "rt-pzaas-cta-offers-v1/artifacts/v1.168-max/cta_native_adjusted_sanity_input.json"

print("=== CTA SHARED MAX REAL HTTP TEST ===", flush=True)

required = [
    model / rel / "cta_native_launcher.py",
    stage / "cta_native_launcher.py",
    stage / "cta_spawn_worker.py",
    stage / "cta_router.py",
    shared / "max_runtime_shared/worker_lifecycle.py",
    fixture,
]
for path in required:
    if not path.is_file():
        raise SystemExit(f"STOP: Missing file: {path}")

request = json.loads(fixture.read_text())
if not isinstance(request, dict):
    raise SystemExit("STOP: CTA request is not a JSON object")

print("ORIGINAL CTA INPUT: FOUND")
print("SHARED CTA WIRING: PRESENT")
print("MAX IMAGE: localhost/max-shared-runtime:cpu")

inside = r'''
import json
import socket
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

logfile = Path("/tmp/cta_shared_max.log")
server = None

try:
    with logfile.open("w") as log:
        server = subprocess.Popen(
            [
                sys.executable, "-u", "-m",
                "maxserve_cta_extension.cta_native_launcher"
            ],
            stdout=log,
            stderr=subprocess.STDOUT
        )

        ready = False
        for _ in range(180):
            if server.poll() is not None:
                break
            try:
                with socket.create_connection(
                    ("127.0.0.1", 8000), timeout=1
                ):
                    ready = True
                    break
            except OSError:
                time.sleep(1)

        if not ready:
            raise RuntimeError("CTA MAX server did not start")

        print("CTA SHARED SERVER: READY", flush=True)

        body = Path("/tmp/cta_input.json").read_bytes()
        req = urllib.request.Request(
            "http://127.0.0.1:8000/cta/predict",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=240) as response:
                status = response.status
                result = json.loads(response.read())
        except urllib.error.HTTPError as error:
            detail = error.read().decode(errors="replace")
            raise RuntimeError(
                f"HTTP {error.code}: {detail[:1000]}"
            )

        if status != 200:
            raise RuntimeError(f"HTTP status {status}")

        if not isinstance(result, (dict, list)) or not result:
            raise RuntimeError("Empty or invalid CTA JSON response")

        if isinstance(result, dict) and (
            result.get("error") or result.get("detail")
        ):
            raise RuntimeError(f"CTA returned an error: {str(result)[:500]}")

        print("HTTP STATUS:", status, flush=True)
        print("CTA REAL JSON RESPONSE: PASS", flush=True)

        if isinstance(result, dict):
            print("RESPONSE FIELDS:", sorted(result.keys()), flush=True)

        print("CTA SHARED MAX HTTP: PASS", flush=True)

except Exception as exc:
    print("CTA SHARED MAX HTTP: BLOCKED", flush=True)
    print("ERROR:", exc, flush=True)
    print("=== SERVER LOG ===", flush=True)
    if logfile.exists():
        print(
            "\n".join(
                logfile.read_text(errors="replace").splitlines()[-55:]
            ),
            flush=True
        )
    sys.exit(1)

finally:
    if server is not None and server.poll() is None:
        server.terminate()
        try:
            server.wait(timeout=8)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait()
'''

pythonpath = ":".join([
    "/shared_infra/python",
    f"/workspace/{rel.parent}",
    f"/workspace/{rel}",
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
    cmd += ["-v", f"{deps}:/shared_deps:ro"]

cmd += [
    "--entrypoint", "/opt/venv/bin/python",
    "localhost/max-shared-runtime:cpu",
    "-u", "-c", inside
]

try:
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=480
    )
except subprocess.TimeoutExpired:
    raise SystemExit("STOP: CTA shared HTTP timed out")

print(result.stdout[-14000:], flush=True)

if result.returncode:
    raise SystemExit("STOP: CTA shared HTTP needs correction")

print("\n=== RESULT ===")
print("CTA SHARED MAX HTTP: PASS")
print("ORIGINAL CTA / BPLAN / PZAAS: UNCHANGED")
print("NEXT: SIMULTANEOUS THREE-MODEL VALIDATION")
PY
