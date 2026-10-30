POD="podman --root /application1/podman/storage --runroot /run/containers/storage"

CID=$($POD ps --format '{{.ID}} {{.Image}}' | awk '$2 ~ /cta-max-faiss/ {print $1; exit}')

if [ -n "$CID" ]; then
  echo "=== LIVE MAX WORKER LOGS ==="
  $POD logs --tail 60 "$CID" 2>&1
else
  echo "MAX CONTAINER NOT FOUND"
fi
