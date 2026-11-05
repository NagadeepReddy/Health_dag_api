
cd /application1/sajjna8/rt-pzaas-v1.0 && {
echo "=== PZAAS NATIVE RUNTIME READINESS ==="

echo "=== CUSTOM PODMAN IMAGES ==="
podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  images --format '{{.Repository}}:{{.Tag}}' 2>&1 | head -25

echo "=== DEFAULT PODMAN IMAGES ==="
podman images --format '{{.Repository}}:{{.Tag}}' 2>&1 | head -15

echo "=== NATIVE LAUNCH FILES ==="
find artifacts/v1.472-max/maxserve_pzaas_extension \
  -maxdepth 3 -type f \
  \( -iname '*launch*.py' -o -iname '*entrypoint*' -o \
  -iname 'Dockerfile*' -o -iname '*.sh' \) \
  -print | sort

echo "=== NATIVE STARTUP CONFIGURATION ==="
grep -RnE \
  'max[.]serve|podman run|model-path|model_path|1876[0-9]|/v2/cta|pzaas_native_launcher' \
  artifacts/v1.472-max/maxserve_pzaas_extension \
  --include='*.py' --include='*.sh' \
  --include='Dockerfile*' 2>/dev/null | head -55

echo "=== PROGRESS ==="
echo "MAX CPU: PASS"
echo "LAYER-0: PASS"
echo "EIGHT BRANCHES: 8/8 PASS"
echo "FULL MODEL PARITY: PASS"
echo "FACTORY / WORKER PARAMETERS: ALIGNED"
echo "NATIVE HTTP 200: PENDING"
echo "NEXT: START REAL NATIVE MAX CONTAINER"
}
