cd /application1/sajjna8/rt-pzaas-v1.0 && {
echo "=== PZAAS CORRECT RUNTIME DISCOVERY ==="

echo "=== PODMAN STORAGE ==="
ls -ld /application1/podman/storage /run/containers/storage 2>&1

echo "=== EXISTING CONTAINERS ==="
podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  ps -a --format 'NAME={{.Names}} IMAGE={{.Image}} STATUS={{.Status}}'

echo "=== EXISTING IMAGES ==="
podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  images --format '{{.Repository}}:{{.Tag}}'

echo "=== HOST PYTHON ==="
for p in /opt/venv/bin/python /usr/local/bin/python3 /usr/bin/python3; do
  if [ -x "$p" ]; then
    echo "PYTHON: $p"
    "$p" -c 'import torch; print("TORCH:",torch.__version__)' 2>&1 | tail -2
  fi
done

echo "=== ORIGINAL DS: UNCHANGED ==="
echo "=== CTA / BPLAN: UNCHANGED ==="
}
