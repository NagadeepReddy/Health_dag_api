
cd /application1/sajjna8/rt-pzaas-v1.0 && bash <<'SH'
set -euo pipefail

HANDOFF="/application1/sajjna8/PZAAS_MAX_CLEAN_HANDOFF_20261106"
EVIDENCE="$PWD/artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_http_evidence"
FIXTURE="$PWD/artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev/pzaas_adjusted_sanity_input.json"
REFERENCE="$EVIDENCE/pzaas_native_response.json"

for path in \
  "$HANDOFF/model" \
  "$HANDOFF/runtime/python_deps" \
  "$HANDOFF/runtime/launch_max_model.sh" \
  "$HANDOFF/config/model.env" \
  "$FIXTURE" \
  "$REFERENCE"; do
  test -e "$path" || {
    echo "STOP: Missing $path"
    exit 1
  }
done

bash -n "$HANDOFF/runtime/launch_max_model.sh"
source "$HANDOFF/config/model.env"

test "$MODULE" = "pzaas_native_serve_dev.pzaas_native_launcher"
test "$INTERNAL_PORT" = "18768"

echo "GENERIC LAUNCHER SYNTAX: PASS"
echo "PACKAGED MODEL CONFIGURATION: PASS"

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  --memory=12g --pids-limit=512 \
  -v "$HANDOFF/model:/workspace:ro" \
  -v "$HANDOFF/runtime/python_deps:/shared_deps:ro" \
  -v "$FIXTURE:/tmp/pzaas_input.json:ro" \
  -v "$REFERENCE:/tmp/pzaas_reference.json:ro" \
  -v "$EVIDENCE:/evidence:rw" \
  -w /workspace \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e "PYTHONPATH=$MODEL_PYTHONPATH" \
  --entrypoint /opt/venv/bin/python \
  localhost/max-shared-runtime:cpu -u - <<'PY'
import json
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

log = Path("/evidence/pzaas_packaged_cold_start.log")
proof = Path("/evidence/pzaas_packaged_cold_start_proof.json")

def unpack(value):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except ValueError:
            return value
    return value

def get_products(payload):
    data = unpack(payload["jsonData"])
    prediction = unpack(data["prediction"])
    result = unpack(prediction["productList"])
    if not isinstance(result, list):
        raise ValueError("Invalid productList")
    return result

print("=== PACKAGED PZAAS COLD START ===", flush=True)

with log.open("w") as output:
    server = subprocess.Popen(
        [
            sys.executable,
            "-u",
            "-m",
            "pzaas_native_serve_dev.pzaas_native_launcher"
        ],
        stdout=output,
        stderr=subprocess.STDOUT
    )

try:
    deadline = time.monotonic() + 150

    while time.monotonic() < deadline:
        if server.poll() is not None:
            raise RuntimeError("Packaged MAX server exited")

        try:
            with socket.create_connection(
                ("127.0.0.1", 18768), timeout=2
            ):
                break
        except OSError:
            time.sleep(2)
    else:
        raise RuntimeError("Packaged MAX startup timeout")

    print("PACKAGED MAX SERVER: READY", flush=True)

    request = urllib.request.Request(
        "http://127.0.0.1:18768/pzaas/predict",
        data=Path("/tmp/pzaas_input.json").read_bytes(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(
        request, timeout=180
    ) as response:
        status = response.status
        payload = json.loads(response.read())

    actual = get_products(payload)
    expected = get_products(
        json.loads(
            Path("/tmp/pzaas_reference.json").read_text()
        )
    )

    execution = (
        "PZAAS REAL MAX EXECUTION: PASS"
        in log.read_text(errors="replace")
    )

    parity = actual == expected

    print("PACKAGED HTTP STATUS:", status)
    print("RECOMMENDATIONS:", len(actual))
    print("SAVED PRODUCT PARITY:", parity)
    print("TRAINED MAX EXECUTION:", execution)

    if not (
        status == 200
        and len(actual) == 24
        and parity
        and execution
    ):
        raise RuntimeError("Packaged acceptance checks failed")

    proof.write_text(json.dumps({
        "packaged_http_status": status,
        "recommendation_count": len(actual),
        "saved_product_parity": parity,
        "trained_max_execution": execution,
        "runtime_source": "packaged handoff only",
        "image": "localhost/max-shared-runtime:cpu",
        "network": "isolated",
        "live_kubernetes_lookups": "not validated"
    }, indent=2))

    print("PZAAS PACKAGED COLD START: PASS")
    print("BUNDLED RUNTIME: PASS")
    print("EVIDENCE:", proof)
    print("ORIGINAL DS / CTA / BPLAN: UNCHANGED")

except Exception as exc:
    print("PACKAGED VERIFICATION BLOCKED:", repr(exc))

    if isinstance(exc, urllib.error.HTTPError):
        print(
            "HTTP ERROR:",
            exc.read(800).decode(errors="replace")
        )

    lines = log.read_text(errors="replace").splitlines()
    print("=== FIRST ROOT ERROR ===")

    for index, line in enumerate(lines):
        if any(term in line for term in (
            "FileNotFoundError",
            "ModuleNotFoundError",
            "ImportError",
            "KeyError",
            "AttributeError"
        )):
            print(
                "\n".join(
                    lines[max(0, index-3):index+5]
                )
            )
            break

    print("=== LAST 25 SERVER LOG LINES ===")
    print("\n".join(lines[-25:]))
    raise SystemExit(1)

finally:
    if server.poll() is None:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait()
PY
SH
