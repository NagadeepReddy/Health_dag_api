
cd /application1/sajjna8 && podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  --memory=18g --pids-limit=512 \
  -v /application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030:/workspace:ro \
  -v /application1/sajjna8/max_shared_infra/isolated/cta_shared_wiring_v1:/workspace/artifacts/v1.168-max/cta_native_batch2_release_candidate/maxserve_cta_extension:ro \
  -v /application1/sajjna8/max_shared_infra/python:/shared_infra/python:ro \
  -v /application1/max_shared_python_deps:/shared_deps:ro \
  -v /application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max/cta_native_adjusted_sanity_input.json:/tmp/cta_input.json:ro \
  -w /workspace \
  -e PYTHONPATH=/shared_infra/python:/workspace/artifacts/v1.168-max/cta_native_batch2_release_candidate:/workspace/artifacts/v1.168-max:/workspace/artifacts/v1.168/core-artifact:/workspace:/shared_deps/sklearn161:/shared_deps \
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

port = 18767
logfile = Path("/tmp/cta_shared_http.log")

command = [
    sys.executable, "-B", "-u", "-c",
    "from maxserve_cta_extension.cta_queue_compat import install; "
    "assert install(); "
    "from maxserve_cta_extension.cta_native_launcher import main; "
    "main()",
    "--port", str(port),
    "--model-path", "/workspace/artifacts/v1.168-max/cta_native_model",
    "--devices", "cpu",
    "--max-batch-size", "2",
]

print("=== CTA SHARED MAX CORRECT ENDPOINT TEST ===", flush=True)
server = None
passed = False

try:
    with logfile.open("w") as log:
        server = subprocess.Popen(
            command, stdout=log, stderr=subprocess.STDOUT
        )

        for attempt in range(180):
            if server.poll() is not None:
                raise RuntimeError("CTA server exited during startup")
            try:
                with socket.create_connection(
                    ("127.0.0.1", port), timeout=1
                ):
                    break
            except OSError:
                time.sleep(1)
        else:
            raise RuntimeError("CTA server not ready")

        print("CTA SHARED SERVER: READY", flush=True)

        url = f"http://127.0.0.1:{port}/v2/cta/predict"
        print("TEST ENDPOINT:", url, flush=True)

        request = urllib.request.Request(
            url,
            data=Path("/tmp/cta_input.json").read_bytes(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(
                request, timeout=240
            ) as response:
                status = response.status
                body = response.read()
        except urllib.error.HTTPError as error:
            detail = error.read().decode(errors="replace")
            raise RuntimeError(
                f"HTTP {error.code}: {detail[:800]}"
            )

        result = json.loads(body)

        if status != 200:
            raise RuntimeError(f"Unexpected HTTP {status}")

        if not isinstance(result, (dict, list)) or not result:
            raise RuntimeError("Invalid or empty JSON")

        if isinstance(result, dict) and (
            "error" in result or "detail" in result
        ):
            raise RuntimeError(str(result)[:800])

        print("HTTP STATUS: 200", flush=True)
        print("REAL CTA JSON: PASS", flush=True)
        print("CTA SHARED MAX HTTP: PASS", flush=True)

        if isinstance(result, dict):
            print("RESPONSE KEYS:", list(result.keys()), flush=True)

        passed = True

except Exception as error:
    print("CTA SHARED MAX HTTP: BLOCKED", flush=True)
    print("ERROR:", error, flush=True)

    if logfile.exists():
        print("=== LAST SERVER LOG ===", flush=True)
        print("\n".join(
            logfile.read_text(errors="replace").splitlines()[-35:]
        ), flush=True)

finally:
    if server is not None and server.poll() is None:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait()

if not passed:
    sys.exit(1)

print("NEXT: SIMULTANEOUS CTA / BPLAN / PZAAS TEST")
PY
