P="podman --root /application1/podman/storage --runroot /run/containers/storage"

$P start cta-native-live >/dev/null

for i in $(seq 1 15); do
  echo "=== WORKER SNAPSHOT $i ==="
  $P top cta-native-live pid ppid comm 2>&1
  sleep 1
done

echo "=== FINAL CONTAINER STATE ==="
$P inspect cta-native-live \
  --format 'Running={{.State.Running}} Exit={{.State.ExitCode}} OOMKilled={{.State.OOMKilled}}'

echo "=== WORKER FAILURE LOG ==="
$P logs --tail 45 cta-native-live 2>&1
