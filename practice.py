cd /application1/sajjna8/rt-pzaas-cta-offers-v1

P="podman --root /application1/podman/storage --runroot /run/containers/storage"

$P run -d --replace --name cta-native-live \
  --pull=never --network=none \
  -v "$PWD:/workspace:Z" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -u /workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_live_server.py

sleep 5

$P ps -a --filter name=cta-native-live
$P logs --tail 70 cta-native-live
