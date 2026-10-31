PODMAN="podman --root /application1/podman/storage --runroot /run/containers/storage"

echo "=== LATEST CTA EXECUTION ==="
$PODMAN logs --timestamps --tail 500 \
  cta-clean-native-batch2 2>&1 |
grep -E \
'CTA PREDICT RAW|CTA RESPONSE SOCKET|CTA RESPONSE ID MATCH|CTA PREDICT EXCEPTION|CTA HTTP QUEUE ITEM|FileNotFoundError|AssertionError|killed|OOM' |
tail -40

echo "=== CONTAINER STATUS ==="
$PODMAN inspect cta-clean-native-batch2 \
  --format 'STATUS={{.State.Status}} PID={{.State.Pid}}'
