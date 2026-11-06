
cd /application1/sajjna8/rt-pzaas-v1.0 && bash <<'SH'
set -euo pipefail

EVIDENCE="$PWD/artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_http_evidence"
mkdir -p "$EVIDENCE"
chmod 700 "$EVIDENCE"

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  --memory=12g --pids-limit=512 \
  -v "$PWD:/workspace:ro" \
  -v "$EVIDENCE:/evidence:rw" \
  -v /application1/max_shared_python_deps:/shared_deps:ro \
  -w /workspace \
  -e PYTHONPATH=/shared_deps/sklearn161:/shared_deps:/workspace/artifacts/v1.472-max/pzaas_max/validation/python_deps:/workspace/artifacts/v1.472-max/maxserve_pzaas_extension:/workspace/artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev:/workspace/artifacts/v1.472-max:/workspace/artifacts/v1.472/core-artifact:/workspace/artifacts/v1.472/utils/dependency-utils \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PY'
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

os.umask(0o077)

fixture = Path(
    "/workspace/artifacts/v1.472-max/"
    "maxserve_pzaas_extension/pzaas_native_serve_dev/"
    "pzaas_adjusted_sanity_input.json"
)
log = Path("/evidence/pzaas_native_http.log")
saved = Path("/evidence/pzaas_native_response.json")

if not fixture.is_file():
    raise SystemExit("STOP: Adjusted fixture missing")

def describe(value):
    if isinstance(value, dict):
        return "dict keys=" + str(list(value.keys())[:20])
    if isinstance(value, list):
        return "list length=" + str(len(value))
    if isinstance(value, str):
        return "string length=" + str(len(value))
    return type(value).__name__

with log.open("w") as output:
    server = subprocess.Popen(
        [
            sys.executable, "-u", "-m",
            "pzaas_native_serve_dev.pzaas_native_launcher"
        ],
        stdout=output,
        stderr=subprocess.STDOUT
    )

try:
    deadline = time.monotonic() + 150

    while time.monotonic() < deadline:
        if server.poll() is not None:
            raise RuntimeError("MAX Serve exited unexpectedly")
        try:
            with socket.create_connection(
                ("127.0.0.1", 18768), timeout=2
            ):
                break
        except OSError:
            time.sleep(2)
    else:
        raise RuntimeError("MAX HTTP startup timeout")

    request = urllib.request.Request(
        "http://127.0.0.1:18768/pzaas/predict",
        data=fixture.read_bytes(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(
        request, timeout=180
    ) as response:
        print("PZAAS HTTP STATUS:", response.status, flush=True)
        payload = json.loads(response.read())

    saved.write_text(json.dumps(payload, indent=2))

    print("PZAAS RESPONSE:", describe(payload))
    if isinstance(payload, dict):
        for key in ("jsonData", "transactionMetadata"):
            value = payload.get(key)
            if isinstance(value, str):
                try:
                    value = json.loads(value)
                except (ValueError, TypeError):
                    pass

            print(key + ":", describe(value))

            if isinstance(value, dict):
                for nested_key, nested_value in list(value.items())[:15]:
                    print(
                        "  " + str(nested_key) + ":",
                        describe(nested_value)
                    )
            elif isinstance(value, list) and value:
                print("  first item:", describe(value[0]))

    lines = log.read_text(errors="replace").splitlines()
    records = [
        line.strip() for line in lines
        if any(marker in line for marker in (
            "PZAAS REAL MAX",
            "PZAAS MAX BASE HOOK",
            "PZAAS PREDICT",
            "Traceback",
            "ERROR"
        ))
    ]

    print("=== REAL MAX EXECUTION EVIDENCE ===")
    for line in records[-20:]:
        print(line[:300])

    completed = any(
        "PZAAS REAL MAX EXECUTION: PASS" in line
        for line in lines
    )

    print(
        "PZAAS TRAINED MAX EXECUTION:",
        "CONFIRMED" if completed else "NOT YET CONFIRMED"
    )
    print("PZAAS RESPONSE FILE:", saved)
    print("PZAAS SERVER LOG:", log)

except Exception as exc:
    print("PZAAS VALIDATION BLOCKED:", repr(exc))
    print("=== LAST 30 SERVER LOG LINES ===")
    print(
        "\n".join(
            log.read_text(errors="replace").splitlines()[-30:]
        )
    )
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
