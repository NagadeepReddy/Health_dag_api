cd /application1/sajjna8/rt-pzaas-cta-offers-v1

P="podman --root /application1/podman/storage --runroot /run/containers/storage"

$P stop -t 5 cta-native-live >/dev/null 2>&1 || true

$P run -d --rm --name cta-native-live \
  --pull=never --network=none \
  -v "$PWD:/workspace:Z" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -u /workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_live_server.py

sleep 8

$P logs cta-native-live 2>&1 | \
grep -E 'startup complete|Uvicorn running|CTA QUEUE INITIALIZED|Traceback|ERROR' | tail -10
