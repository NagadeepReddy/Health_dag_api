cd /application1/sajjna8/rt-pzaas-cta-offers-v1

timeout -k 10s 180s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  -v "$PWD:/workspace:Z" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u \
  /workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_e2e_test.py \
  > /tmp/cta_extended_e2e.log 2>&1

rc=$?
echo "ACTUAL TEST EXIT CODE: $rc"
grep -E 'CTA REQUEST RECEIVED|CTA WORKER RESPONSE IDS: \[.|CTA NATIVE HTTP STATUS|CTA RESPONSE:|Traceback|ValidationError|RuntimeError' \
  /tmp/cta_extended_e2e.log | tail -12
