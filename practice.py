set -e

PODMAN="podman --root /application1/podman/storage --runroot /run/containers/storage"
NAME="cta-clean-batch2-http-20261030"
CLEAN="/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030"

test -f "$CLEAN/artifacts/v1.168-max/real_max_batch2_backend.py"

AVAILABLE=$(awk '/^MemAvailable:/ {print $2}' /proc/meminfo)
test "$AVAILABLE" -ge 18874368 || {
  echo "STOP: Insufficient host memory"
  exit 1
}

# Confirm this is our disposable test container.
MOUNT=$($PODMAN inspect "$NAME" \
  --format '{{range .Mounts}}{{if eq .Destination "/workspace"}}{{.Source}}{{end}}{{end}}')

test "$MOUNT" = "$CLEAN" || {
  echo "STOP: Container does not belong to clean test"
  exit 1
}

$PODMAN stop -t 10 "$NAME"
$PODMAN rm "$NAME"

$PODMAN run -d \
  --name "$NAME" \
  --pull=never \
  --memory=14g \
  --cpus=4 \
  --pids-limit=256 \
  --network=none \
  --tmpfs /tmp:rw,size=2g \
  --tmpfs /root:rw,size=64m \
  -v "$CLEAN:/workspace:ro" \
  -v "$CLEAN/artifacts/v1.168-max:/batch2:ro" \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max/cta_native_batch2_release_candidate:/workspace/artifacts/v1.168/core-artifact:/batch2:/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -B -u -c 'import time; print("CACHE-WRITABLE TEST CONTAINER READY", flush=True); time.sleep(1200)'

echo "CLEAN TEST CONTAINER REPLACED"
