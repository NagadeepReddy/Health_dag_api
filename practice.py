cd /application1/sajjna8/rt-pzaas-cta-offers-v1

set -o pipefail
timeout 65s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  -v "$PWD:/workspace:Z" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -u /workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_e2e_test.py \
  2>&1 | tee /tmp/cta_wire_fix_e2e.log | \
  grep --line-buffered -E 'CTA REQUEST RECEIVED|CTA WORKER RESPONSE IDS|CTA NATIVE HTTP STATUS|CTA RESPONSE:|CTA NATIVE END-TO-END|KeyError|Error|Traceback|EXIT CODE'

echo "TEST EXIT CODE: ${PIPESTATUS[0]}"
