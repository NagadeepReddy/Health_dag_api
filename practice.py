cd /application1/sajjna8/rt-pzaas-cta-offers-v1

timeout 50s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  -v "$PWD:/workspace:Z" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -u /workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_e2e_test.py \
  > /tmp/cta_queue_fix_test.log 2>&1

rc=$?
echo "=== NATIVE CTA RESULT ==="
grep -E 'CTA MAX REQUEST UNWRAPPED|CTA REQUEST RECEIVED|CTA NATIVE HTTP STATUS|CTA RESPONSE:|KeyError|TypeError|ValueError|Traceback|Error' \
  /tmp/cta_queue_fix_test.log | tail -15
echo "EXIT CODE: $rc"
