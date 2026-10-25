P="podman --root /application1/podman/storage --runroot /run/containers/storage"

echo "=== CONTAINER STATE ==="
$P inspect cta-native-live \
  --format 'Running={{.State.Running}} ExitCode={{.State.ExitCode}}'

echo "=== STARTUP DETAILS ==="
$P logs --tail 100 cta-native-live 2>&1 | \
  grep -Ev 'CTA WORKER RESPONSE IDS: \[\]|not use pretrained embedding' | tail -40
