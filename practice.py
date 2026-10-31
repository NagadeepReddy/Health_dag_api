PODMAN="podman --root /application1/podman/storage --runroot /run/containers/storage"
NAME="cta-clean-batch2-http-20261030"

test "$($PODMAN inspect "$NAME" --format '{{.State.Status}}')" = "running" || {
  echo "STOP: Clean container not running"
  exit 1
}

AVAILABLE=$(awk '/^MemAvailable:/ {print $2}' /proc/meminfo)
test "$AVAILABLE" -ge 18874368 || {
  echo "STOP: Insufficient host RAM"
  exit 1
}

$PODMAN exec "$NAME" /opt/venv/bin/python -B - <<'PY'
from pathlib import Path
import os, socket

base = Path("/workspace/artifacts/v1.168-max/cta_max")
for name in ("nlp_bert_max.py", "sequence_pooling_max.py"):
    assert (base / name).is_file(), f"STOP: Missing {name}"

s = socket.socket()
s.settimeout(2)
assert s.connect_ex(("127.0.0.1", 18767)) != 0, "STOP: Server already listening"
s.close()

for proc in Path("/proc").iterdir():
    if not proc.name.isdigit() or int(proc.name) == os.getpid():
        continue
    try:
        cmd = (proc / "cmdline").read_bytes().replace(b"\0", b" ")
        if b"cta_native_launcher" in cmd and b"main()" in cmd:
            raise SystemExit("STOP: Native server process already exists")
    except (OSError, PermissionError):
        continue

print("SAFE TO START: PASS")
PY

test "$?" -eq 0 || exit 1

$PODMAN exec -d \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max/cta_native_batch2_release_candidate:/workspace/artifacts/v1.168/core-artifact:/batch2:/workspace/artifacts/v1.168-max \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e PYTHONUNBUFFERED=1 \
  -e CUDA_VISIBLE_DEVICES= \
  -e HOME=/tmp \
  -e TMPDIR=/tmp \
  -e XDG_CACHE_HOME=/tmp/cta_batch2_cache \
  -e HF_HOME=/tmp/cta_batch2_cache \
  -e TORCH_HOME=/tmp/cta_batch2_cache \
  -e OTEL_SDK_DISABLED=true \
  -e OTEL_METRICS_EXPORTER=none \
  -e OTEL_TRACES_EXPORTER=none \
  -e OTEL_LOGS_EXPORTER=none \
  "$NAME" \
  /bin/sh -c 'timeout -s TERM -k 10s 360s /opt/venv/bin/python -B -u -c "from maxserve_cta_extension.cta_queue_compat import install; assert install(); from maxserve_cta_extension.cta_native_launcher import main; main()" --port 18767 --model-path /workspace/artifacts/v1.168-max/cta_native_model --devices cpu --max-batch-size 2 > /tmp/cta_clean_http.log 2>&1'
