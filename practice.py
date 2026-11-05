
cd /application1/sajjna8/rt-pzaas-v1.0 && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm -i --pull=never --network=none \
--memory=12g --pids-limit=512 \
-v "$PWD:/workspace:ro" \
-v /application1/max_shared_python_deps:/shared_deps:ro \
-w /workspace \
-e PYTHONPATH=/shared_deps/sklearn161:/shared_deps:/workspace/artifacts/v1.472-max/pzaas_max/validation/python_deps:/workspace/artifacts/v1.472-max/maxserve_pzaas_extension:/workspace/artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev:/workspace/artifacts/v1.472-max:/workspace/artifacts/v1.472/core-artifact:/workspace/artifacts/v1.472/utils/dependency-utils \
--entrypoint /opt/venv/bin/python \
localhost/cta-max-faiss:local -u - <<'PY'
import json
import socket
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

log_path = Path("/tmp/pzaas_native_http.log")
fixture = Path("/workspace/artifacts/v1.472/samples/sanity_input.json")

def show_logs():
    if log_path.exists():
        print("=== NATIVE MAX SERVER LOG (LAST 35 LINES) ===", flush=True)
        print("\n".join(log_path.read_text(errors="replace").splitlines()[-35:]), flush=True)

if not fixture.is_file():
    raise SystemExit("ERROR: Real PZAAS JSON fixture missing")

payload = json.loads(fixture.read_text())
log = log_path.open("w")

print("PZAAS BUILT-IN MAX SERVE: STARTING", flush=True)

p = subprocess.Popen(
    [
        sys.executable, "-u", "-m",
        "pzaas_native_serve_dev.pzaas_native_launcher"
    ],
    stdout=log,
    stderr=subprocess.STDOUT
)
log.close()

try:
    deadline = time.monotonic() + 150
    ready = False

    while time.monotonic() < deadline:
        if p.poll() is not None:
            raise RuntimeError("Native MAX server exited during startup")
        try:
            with socket.create_connection(("127.0.0.1", 18768), timeout=2):
                ready = True
                break
        except OSError:
            time.sleep(2)

    if not ready:
        raise RuntimeError("Native MAX HTTP port did not become ready")

    print("PZAAS NATIVE HTTP PORT: READY", flush=True)

    request = urllib.request.Request(
        "http://127.0.0.1:18768/pzaas/predict",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=180) as response:
        body = response.read()
        result = json.loads(body)
        print("PZAAS REAL HTTP STATUS:", response.status, flush=True)
        print("PZAAS RESPONSE TYPE:", type(result).__name__, flush=True)
        if isinstance(result, dict):
            print("PZAAS RESPONSE KEYS:", list(result), flush=True)
        assert response.status == 200
        print("PZAAS BUILT-IN MAX HTTP 200: PASS", flush=True)

except Exception as exc:
    print("PZAAS HTTP TEST BLOCKED:", repr(exc), flush=True)
    if isinstance(exc, urllib.error.HTTPError):
        print("HTTP ERROR BODY:", exc.read(1000).decode(errors="replace"))
    show_logs()
    raise SystemExit(1)

finally:
    p.terminate()
    try:
        p.wait(timeout=5)
    except subprocess.TimeoutExpired:
        p.kill()
        p.wait()
PY
