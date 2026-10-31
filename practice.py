PODMAN="podman --root /application1/podman/storage --runroot /run/containers/storage"
NAME="cta-postman-shm1g-test"
REPO="/application1/sajjna8/rt-pzaas-cta-offers-v1"
DEV="/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029"
PKG="/application1/cta_max_true_batch_dev_20261028/batch2_candidate/cta_max"

if [ "$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)" -lt 18874368 ]; then
  echo "STOP: Insufficient host RAM"
elif $PODMAN container exists "$NAME"; then
  echo "STOP: Container already exists"
else
  $PODMAN create \
    --pull=never \
    --name "$NAME" \
    --memory=14g \
    --memory-swap=14g \
    --shm-size=1g \
    --cpus=4 \
    --pids-limit=256 \
    --network=bridge \
    -p 127.0.0.1:18767:18767 \
    --tmpfs /tmp:rw,size=2g,mode=1777 \
    -v "$REPO:/workspace:ro" \
    -v "$DEV/real_max_batch2_backend.py:/batch2/real_max_batch2_backend.py:ro" \
    -v "$PKG:/batch2/cta_max:ro" \
    --entrypoint /opt/venv/bin/python \
    localhost/cta-max-faiss:local \
    -B -u -c 'import time; time.sleep(1800)'
fi
