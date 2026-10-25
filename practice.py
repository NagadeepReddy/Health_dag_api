P="podman --root /application1/podman/storage --runroot /run/containers/storage"

sleep 20

$P ps -a --filter name=cta-native-live

$P logs --tail 60 cta-native-live 2>&1 | \
grep -E 'CTA_RESPONSE_WORKER_STARTED|CTA QUEUE INITIALIZED|startup complete|Uvicorn running|Traceback|Error|ERROR' | tail -20
