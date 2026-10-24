cd /application1/sajjna8/rt-pzaas-cta-offers-v1

timeout 45s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  -v "$PWD:/workspace:Z" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -u /workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_e2e_test.py \
  > /tmp/cta_context_test.log 2>&1

rc=$?

echo "=== CTA REQUEST AND RESPONSE ==="
grep -E 'CTA REQUEST RECEIVED|CTA WORKER RESPONSE IDS|CTA NATIVE HTTP STATUS|CTA RESPONSE:|CTA NATIVE END-TO-END|ValidationError|TypeError|Traceback' \
  /tmp/cta_context_test.log | tail -15

echo "TEST EXIT CODE: $rc"
