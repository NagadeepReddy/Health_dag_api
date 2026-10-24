cd /application1/sajjna8/rt-pzaas-cta-offers-v1

timeout -k 5s 45s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  -v "$PWD:/workspace:Z" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -u /workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_e2e_test.py \
  > /tmp/cta_final_verify.log 2>&1

rc=$?
echo "=== CTA NATIVE E2E RESULT ==="
grep -E 'CTA REQUEST RECEIVED|CTA WORKER RESPONSE IDS: \[.|CTA NATIVE HTTP STATUS|CTA RESPONSE:|CTA NATIVE END-TO-END|ValidationError|KeyError|TypeError|RuntimeError|Traceback' \
  /tmp/cta_final_verify.log | tail -12
echo "EXIT CODE: $rc"
