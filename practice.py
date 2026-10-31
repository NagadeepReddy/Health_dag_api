PODMAN="podman --root /application1/podman/storage --runroot /run/containers/storage"

echo "=== REFERENCE RESTORED ==="
test -d /application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030/batch2/cta_max &&
echo "REFERENCE: RESTORED"

echo "=== CONTAINER STATUS ==="
$PODMAN ps -a --filter name=cta-clean-native-batch2

echo "=== LATEST WORKER ERRORS ==="
$PODMAN logs --timestamps --since 30m --tail 300 \
  cta-clean-native-batch2 2>&1 |
grep -Ei 'error|exception|timeout|missing|failed|predict|response|killed' |
tail -50
