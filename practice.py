cd /application1/sajjna8/rt-pzaas-cta-offers-v1

PODMAN="podman --root /application1/podman/storage --runroot /run/containers/storage"

CID=$($PODMAN ps -q | head -1)

if [ -n "$CID" ]; then
  echo "=== RUNNING PROCESSES ==="
  $PODMAN top "$CID" pid args

  echo "=== WORKER LOGS ==="
  $PODMAN logs --tail 150 "$CID" 2>&1 |
    grep -Ei 'CTA|scheduler|worker|error|traceback|failed' |
    tail -45
else
  echo "NO RUNNING CONTAINER"
fi
