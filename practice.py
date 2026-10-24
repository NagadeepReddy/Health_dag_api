cd /application1/sajjna8/rt-pzaas-cta-offers-v1

timeout 60s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  -v "$PWD:/workspace:Z" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -u /workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_e2e_test.py \
  > /tmp/cta_fanout.log 2>&1

echo "=== HTTP RESPONSE DIAGNOSTIC ==="
grep -E 'CTA HTTP FANOUT|CTA_NATIVE_RESPONSE_TYPES|CTA NATIVE HTTP STATUS|CTA RESPONSE:|Traceback|Worker failed' \
  /tmp/cta_fanout.log | tail -12
echo "TEST EXIT CODE: $?"
