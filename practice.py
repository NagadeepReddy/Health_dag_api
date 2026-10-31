set -e

PODMAN="podman --root /application1/podman/storage --runroot /run/containers/storage"
CLEAN="/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030"
NAME="cta-clean-batch2-http-20261030"

test -f "$CLEAN/artifacts/v1.168-max/real_max_batch2_backend.py"
test -f "$CLEAN/artifacts/v1.168-max/cta_max/run_batch2_contract.py"

AVAILABLE=$(awk '/^MemAvailable:/ {print $2}' /proc/meminfo)
test "$AVAILABLE" -ge 18874368 || {
  echo "STOP: Less than 18 GiB available RAM"
  exit 1
}

if $PODMAN container exists "$NAME"; then
  echo "STOP: Test container name already exists"
  exit 1
fi

$PODMAN run -d \
  --name "$NAME" \
  --pull=never \
  --memory=14g \
  --cpus=4 \
  --pids-limit=256 \
  --network=none \
  --read-only \
  --tmpfs /tmp:rw,size=2g \
  --tmpfs /root:rw,size=64m \
  -v "$CLEAN:/workspace:ro" \
  -v "$CLEAN/artifacts/v1.168-max:/batch2:ro" \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max/cta_native_batch2_release_candidate:/workspace/artifacts/v1.168/core-artifact:/batch2:/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -B -u -c 'import time; print("CLEAN TEST CONTAINER READY", flush=True); time.sleep(1200)'
