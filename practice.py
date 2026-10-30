POD="podman --root /application1/podman/storage --runroot /run/containers/storage"

CID=$($POD ps --format '{{.ID}} {{.Image}}' | awk '$2 ~ /cta-max-faiss/ {print $1; exit}')

if [ -n "$CID" ]; then
  echo "=== LIVE MAX WORKER PROCESSES ==="
  $POD top "$CID"
else
  echo "NO RUNNING MAX CONTAINER"
fi
