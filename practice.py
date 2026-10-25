P="podman --root /application1/podman/storage --runroot /run/containers/storage"

$P cp cta-native-live:/opt/venv/lib/python3.12/site-packages/max/serve/scheduler/queues.py /tmp/cta_max_queues.py

echo "=== RESPONSE WORKER ERROR HANDLING ==="
sed -n '235,315p' /tmp/cta_max_queues.py

echo "=== FIRST STARTUP FAILURE ==="
$P logs cta-native-live 2>&1 | grep -B 12 -A 8 'Task completed with error' | head -35
