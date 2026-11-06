
cd /application1/sajjna8 && \
BASE=/application1/sajjna8 && \
MODEL="$BASE/PZAAS_MAX_CLEAN_HANDOFF_20261106/model" && \
STAGE="$BASE/max_shared_infra/isolated/pzaas_shared_wiring_v1" && \
INPUT="$BASE/rt-pzaas-v1.0/artifacts/v1.472/samples/ppa_input.json" && \
test -d "$MODEL" && test -f "$STAGE/pzaas_native_launcher.py" && test -f "$INPUT" && \
podman --root /application1/podman/storage --runroot /run/containers/storage \
run --rm -i --pull=never --network=none \
--memory=12g --pids-limit=512 \
-v "$MODEL:/workspace:ro" \
-v "$STAGE:/workspace/artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev:ro" \
-v "$BASE/max_shared_infra/python:/shared_infra/python:ro" \
-v /application1/max_shared_python_deps:/shared_deps:ro \
-v "$INPUT:/input.json:ro" \
-w /workspace \
-e PYTHONPATH=/shared_infra/python:/shared_deps/sklearn161:/shared_deps:/workspace/artifacts/v1.472-max/pzaas_max/validation/python_deps:/workspace/artifacts/v1.472-max/maxserve_pzaas_extension:/workspace/artifacts/v1.472-max:/workspace/artifacts/v1.472/core-artifact:/workspace/artifacts/v1.472/utils/dependency-utils \
--entrypoint /opt/venv/bin/python \
localhost/max-shared-runtime:cpu -u - <<'PY'
import json
import socket
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

payload = json.loads(Path("/input.json").read_text())
assert isinstance(payload, dict)
assert "ClientFeature" in payload

print("=== ISOLATED SHARED MAX E2E ===", flush=True)
print("INPUT: ORIGINAL PZAAS PPA FIXTURE", flush=True)

logpath = Path("/tmp/pzaas_shared_e2e.log")
log = logpath.open("w")

server = subprocess.Popen(
    [
        sys.executable, "-u", "-m",
        "pzaas_native_serve_dev.pzaas_native_launcher"
    ],
    stdout=log,
    stderr=subprocess.STDOUT,
)

try:
    ready = False

    for _ in range(150):
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
        raise RuntimeError("Shared MAX server startup failed")

    print("SHARED MAX SERVER: READY", flush=True)

    request = urllib.request.Request(
        "http://127.0.0.1:18768/pzaas/predict",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            status = response.status
            result = json.loads(response.read())
    except urllib.error.HTTPError as error:
        body = error.read().decode(errors="replace")
        raise RuntimeError(
            f"HTTP {error.code}: {body[:600]}"
        )

    prediction = result.get("jsonData", result)
    if isinstance(prediction, dict):
        prediction = prediction.get("prediction", prediction)

    products = (
        prediction.get("productList")
        if isinstance(prediction, dict)
        else None
    )

    if status != 200:
        raise RuntimeError(f"HTTP status {status}")

    if not isinstance(products, list):
        raise RuntimeError(
            "HTTP 200 but expected productList not found"
        )

    print("\n=== RESULT ===")
    print("SHARED MAX HTTP: 200 PASS")
    print("RECOMMENDATION COUNT:", len(products))
    print("SHARED ROUTER STAGE: ACTIVE")
    print("ORIGINAL DS / WEIGHTS: UNCHANGED")
    print("CTA / BPLAN: UNCHANGED")

    if len(products) == 24:
        print("24 RECOMMENDATIONS: PASS")
    else:
        print("24 RECOMMENDATIONS: NOT MATCHED")

    print("NEXT: VERIFY LIVE SHARED HOOK EXECUTION")

except Exception as exc:
    print("\nSHARED MAX E2E: BLOCKED")
    print("ERROR:", str(exc)[:800])
    log.flush()
    print("\n=== SERVER LOG: LAST 40 LINES ===")
    print("\n".join(
        logpath.read_text(errors="replace").splitlines()[-40:]
    ))
    raise SystemExit(1)

finally:
    server.terminate()
    try:
        server.wait(timeout=5)
    except subprocess.TimeoutExpired:
        server.kill()
        server.wait()
    log.close()
PY
