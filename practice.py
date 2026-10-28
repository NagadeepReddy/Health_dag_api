echo "=== AVAILABLE MAX / FAISS IMAGES ==="

podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  images --format \
  'IMAGE={{.Repository}}:{{.Tag}} ID={{.ID}} SIZE={{.Size}}' \
  | grep -Ei 'max|modular|faiss' || true

echo "=== BACKUP VERIFICATION ==="

cd /application1 || exit 1

sha256sum -c \
  cta_max_native_http_pass_20261028.tar.gz.sha256

echo "NO IMAGES STARTED OR MODIFIED"
