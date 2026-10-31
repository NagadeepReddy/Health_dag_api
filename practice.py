PODMAN="podman --root /application1/podman/storage --runroot /run/containers/storage"
NAME="cta-postman-validated-20261030"

echo "=== CONTAINER ==="
$PODMAN inspect "$NAME" --format 'STATUS={{.State.Status}} OOM_KILLED={{.State.OOMKilled}}'

echo "=== WORKER STARTUP EVIDENCE ==="
$PODMAN exec "$NAME" /bin/sh -c '
grep -nEi "worker.*start|worker.*ready|worker.*failed|worker died|model.*load|response.*timeout|zmq.error|out of memory|killed|traceback" \
/tmp/cta_postman_native.log | tail -n 25
'
