PODMAN="podman --root /application1/podman/storage --runroot /run/containers/storage"
NAME=cta-clean-native-batch2

echo "=== CLEAN CONTAINER ==="
$PODMAN inspect "$NAME" \
  --format 'STATUS={{.State.Status}} EXIT={{.State.ExitCode}} OOM={{.State.OOMKilled}}'

echo "=== LAST REQUEST / WORKER EVENTS ==="
$PODMAN logs --tail 300 "$NAME" 2>&1 | \
  grep -Ei 'CTA|worker|queue|request|response|error|exception|traceback|timeout|failed|killed|shutdown|model|batch' | \
  tail -65
