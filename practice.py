cd /application1/sajjna8/rt-pzaas-v1.0 && {
  echo "=== APSCHEDULER USAGE ==="
  grep -nE 'apscheduler|BackgroundScheduler|scheduler' \
    artifacts/v1.472/core-artifact/pipeline.py | head -30 || true

  echo "=== DEPENDENCY FILES ==="
  find . -maxdepth 5 -type f \
    \( -name 'requirements*.txt' -o -name 'Dockerfile*' \) \
    -print | head -30

  echo "=== AVAILABLE CONTAINER IMAGES ==="
  podman --root /application1/podman/storage \
    --runroot /run/containers/storage \
    images --format '{{.Repository}}:{{.Tag}}' | head -30

  echo "=== LOCAL APSCHEDULER WHEELS ==="
  find /application1/sajjna8 -maxdepth 5 -type f \
    -iname '*apscheduler*.whl' -print | head -10

  echo "DEPENDENCY INSPECTION: COMPLETE"
}
