PODMAN="podman --root /application1/podman/storage --runroot /run/containers/storage"

$PODMAN exec cta-postman-shm1g-test /bin/sh -c '
echo "=== EXPECTED MODEL WEIGHT ==="
ls -l /workspace/artifacts/v1.168-max/cta_max/sequence_weights/fn_norm1_g.npy 2>&1

echo "=== ACTUAL FILE LOCATION ==="
find /workspace/artifacts/v1.168-max \
  -maxdepth 7 -type f -name fn_norm1_g.npy -print

echo "=== CONTAINER WORKING DIRECTORY ==="
pwd
'
