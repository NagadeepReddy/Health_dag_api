
cd /application1/sajjna8/rt-pzaas-v1.0 && bash <<'SH'
set -euo pipefail

STAGE="/application1/sajjna8/PZAAS_MAX_CLEAN_STAGE_20261106"
EVIDENCE="$PWD/artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_http_evidence"
COLLECTION="$EVIDENCE/PZAAS_CLEAN_MAX_POSTMAN_COLLECTION.json"
NAME="pzaas-clean-postman-20261106"

test -d "$STAGE"
test -f "$COLLECTION"

PODMAN=(podman --root /application1/podman/storage --runroot /run/containers/storage)

if "${PODMAN[@]}" container exists "$NAME"; then
    echo "STOP: Container name already exists. Nothing changed."
    exit 1
fi

PORT=$(python3 - <<'PY'
import socket

for port in range(18770, 18790):
    with socket.socket() as sock:
        try:
            sock.bind(("127.0.0.1", port))
        except OSError:
            continue
        print(port)
        break
else:
    raise SystemExit("STOP: No free port found")
PY
)

echo "SELECTED FREE PORT: $PORT"

"${PODMAN[@]}" run -d --pull=never \
  --name "$NAME" \
  --memory=12g --pids-limit=512 \
  -p "127.0.0.1:${PORT}:18768" \
  -v "$STAGE:/workspace:ro" \
  -v /application1/max_shared_python_deps:/shared_deps:ro \
  -w /workspace \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e PYTHONPATH=/shared_deps/sklearn161:/shared_deps:/workspace/artifacts/v1.472-max/pzaas_max/validation/python_deps:/workspace/artifacts/v1.472-max/maxserve_pzaas_extension:/workspace/artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev:/workspace/artifacts/v1.472-max:/workspace/artifacts/v1.472/core-artifact:/workspace/artifacts/v1.472/utils/dependency-utils \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -u -m pzaas_native_serve_dev.pzaas_native_launcher

python3 - "$NAME" "$PORT" "$COLLECTION" <<'PY'
import json
import socket
import subprocess
import sys
import time
from pathlib import Path

name = sys.argv[1]
port = int(sys.argv[2])
collection = Path(sys.argv[3])

podman = [
    "podman",
    "--root", "/application1/podman/storage",
    "--runroot", "/run/containers/storage"
]

print("PZAAS POSTMAN SERVER: STARTING", flush=True)

ready = False

for attempt in range(90):
    result = subprocess.run(
        podman + [
            "inspect", "--format", "{{.State.Running}}", name
        ],
        capture_output=True, text=True
    )

    if result.returncode or result.stdout.strip() != "true":
        print("POSTMAN CONTAINER: EXITED")
        break

    try:
        with socket.create_connection(
            ("127.0.0.1", port), timeout=2
        ):
            ready = True
            break
    except OSError:
        time.sleep(2)

if not ready:
    logs = subprocess.run(
        podman + ["logs", "--tail", "40", name],
        capture_output=True, text=True
    )
    print("=== SERVER LOG ===")
    print(logs.stdout[-4000:])
    print(logs.stderr[-2000:])
    raise SystemExit("POSTMAN SERVER: NOT READY")

data = json.loads(collection.read_text())

if data.get("info", {}).get("name") != "PZAAS v1.472 Clean MAX Serve":
    raise SystemExit("STOP: Unexpected Postman collection")

url = f"http://127.0.0.1:{port}/pzaas/predict"
data["item"][0]["request"]["url"] = url
collection.write_text(json.dumps(data, indent=2))

print("PZAAS POSTMAN SERVER: READY")
print("VM PORT:", port)
print("POSTMAN ENDPOINT:", url)
print("POSTMAN COLLECTION: UPDATED")
print("ORIGINAL DS / CTA / BPLAN: UNCHANGED")
print("EXTERNAL POSTMAN VALIDATION: PENDING")
PY
SH
