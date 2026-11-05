
cd /application1/sajjna8/rt-pzaas-v1.0 && {
echo "=== PZAAS NATIVE RUNTIME READINESS ==="

echo "=== EXISTING MAX IMAGES ==="
podman --root /application1/podman/storage \
--runroot /run/containers/storage \
images --format '{{.Repository}}:{{.Tag}}'

echo "=== EXISTING CONTAINERS ==="
podman --root /application1/podman/storage \
--runroot /run/containers/storage \
ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'

echo "=== PZAAS NATIVE LAUNCH FILES ==="
find artifacts/v1.472-max/maxserve_pzaas_extension \
-maxdepth 3 -type f \
\( -name '*launcher*.py' -o -name '*entrypoint*' \
-o -name 'Dockerfile*' -o -name '*.sh' \) \
-print

echo "=== NATIVE STARTUP REFERENCES ==="
grep -RInE \
'podman run|pzaas_native_launcher|max\.serve|1876[0-9]|/v2/|spawn_worker' \
artifacts/v1.472-max/maxserve_pzaas_extension \
--include='*.py' --include='*.sh' 2>/dev/null | head -50

echo "=== PROGRESS ==="
echo "MAX CPU: PASS"
echo "LAYER-0: PASS"
echo "EIGHT BRANCHES: 8/8 PASS"
echo "FULL MODEL PARITY: PASS"
echo "72-INPUT BRIDGE: PASS"
echo "NATIVE FACTORY: ALIGNED"
echo "NATIVE WORKER RUNTIME: PENDING"
echo "NATIVE HTTP 200: PENDING"
}
