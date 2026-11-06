
cd /application1/sajjna8 && \
BASE=/application1/sajjna8 && \
MODEL="$BASE/PZAAS_MAX_CLEAN_HANDOFF_20261106/model" && \
STAGE="$BASE/max_shared_infra/isolated/pzaas_shared_wiring_v1" && \
COLLECTION="$BASE/rt-pzaas-v1.0/artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_http_evidence/PZAAS_CLEAN_MAX_POSTMAN_COLLECTION.json" && \
test -d "$MODEL" && test -f "$STAGE/pzaas_native_launcher.py" && test -f "$COLLECTION" && \
podman --root /application1/podman/storage --runroot /run/containers/storage \
run --rm -i --pull=never --network=none \
--memory=12g --pids-limit=512 \
-v "$MODEL:/workspace:ro" \
-v "$STAGE:/workspace/artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev:ro" \
-v "$BASE/max_shared_infra/python:/shared_infra/python:ro" \
-v /application1/max_shared_python_deps:/shared_deps:ro \
-v "$COLLECTION:/collection.json:ro" \
-w /workspace \
-e PYTHONPATH=/shared_infra/python:/shared_deps/sklearn161:/shared_deps:/workspace/artifacts/v1.472-max/pzaas_max/validation/python_deps:/workspace/artifacts/v1.472-max/maxserve_pzaas_extension:/workspace/artifacts/v1.472-max:/workspace/artifacts/v1.472/core-artifact:/workspace/artifacts/v1.472/utils/dependency-utils \
--entrypoint /opt/venv/bin/python \
localhost/max-shared-runtime:cpu -u - <<'PY'
import json
import subprocess
import sys
import time
import socket
import urllib.request
from pathlib import Path

collection = json.loads(Path("/collection.json").read_text())

def requests(items):
    for item in items:
        if isinstance(item.get("request"), dict):
            yield item["request"]
        yield from requests(item.get("item", []))

payload = None
for request in requests(collection.get("item", [])):
    body = request.get("body", {})
    if request.get("method") != "POST":
        continue
    raw = body.get("raw") if isinstance(body, dict) else None
    if not raw:
        continue
    try:
        candidate = json.loads(raw)
    except (ValueError, TypeError):
        continue
    if isinstance(candidate, dict) and "jsonData" in candidate:
        payload = candidate
        break

if payload is None:
    raise SystemExit("STOP: Valid PZAAS Postman request not found")

print("SHARED MAX LIVE HTTP: STARTING", flush=True)

log_path = Path("/tmp/pzaas_shared_live_http.log")
log = log_path.open("w")

server = subprocess.Popen(
    [
        sys.executable, "-u", "-m",
        "pzaas_native_serve_dev.pzaas_native_launcher",
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
        raise RuntimeError("MAX Serve did not become ready")

    print("SHARED MAX HTTP PORT: READY", flush=True)

    req = urllib.request.Request(
        "http://127.0.0.1:18768/pzaas/predict",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=180) as response:
        status = response.status
        result = json.load(response)

    products = result.get("jsonData", {}).get(
        "prediction", {}
    ).get("productList", [])

    if status != 200:
        raise RuntimeError(f"Unexpected HTTP status: {status}")

    if not isinstance(products, list) or len(products) != 24:
        raise RuntimeError(
            f"Unexpected recommendations: {len(products)}"
        )

    log.flush()
    evidence = log_path.read_text(errors="replace")

    if not any(marker in evidence for marker in (
        "PZAAS REAL MAX EXECUTION: PASS",
        "PZAAS TRAINED MAX EXECUTION: CONFIRMED",
    )):
        raise RuntimeError(
            "HTTP passed but trained MAX execution not confirmed"
        )

    print("\n=== SHARED MAX END-TO-END RESULT ===")
    print("SHARED COMPONENTS: ISOLATED STAGE")
    print("REAL MAX SERVE: PASS")
    print("HTTP 200: PASS")
    print("TRAINED MAX INFERENCE: PASS")
    print("RECOMMENDATIONS: 24")
    print("ORIGINAL DS / WEIGHTS: UNCHANGED")
    print("ORIGINAL HANDOFFS: UNCHANGED")
    print("NEXT: FINAL SHARED INTEGRATION HANDOFF")

except Exception as exc:
    print("SHARED MAX E2E: BLOCKED:", repr(exc))
    log.flush()
    if log_path.exists():
        print("\n=== LAST SERVER LOG LINES ===")
        print("\n".join(
            log_path.read_text(errors="replace").splitlines()[-35:]
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
