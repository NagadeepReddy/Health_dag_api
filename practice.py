ROOT=/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030
PODMAN="podman --root /application1/podman/storage --runroot /run/containers/storage"

echo "=== ACTIVE CONTAINER MOUNTS ==="
$PODMAN inspect cta-clean-native-batch2 \
  --format '{{range .Mounts}}{{println .Source "=>" .Destination}}{{end}}'

echo "=== EXTERNAL PATH REFERENCES ==="
grep -RInE \
  --include='*.py' --include='*.sh' \
  '(/workspace/batch2|/application1/|CTA_MAX_TRUE_BATCH2_DEV|batch2/cta_max)' \
  "$ROOT/run_cta_native.sh" \
  "$ROOT/artifacts/v1.168-max" \
  2>/dev/null | head -35

echo "=== ACTIVE PACKAGE SYMLINKS ==="
find "$ROOT/artifacts/v1.168-max" -type l -ls

echo "=== REFERENCE FOLDER ==="
test -d "$ROOT/batch2/cta_max" && echo "REFERENCE: PRESENT"
