cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
LOG=/application1/cta_native_envfix_e2e.log && \
timeout 210s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --network=none \
  --memory=8g --memory-swap=8g \
  --pids-limit=64 --cpus=4 \
  --tmpfs /tmp:rw,size=512m \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e OPENBLAS_NUM_THREADS=1 \
  -e OMP_NUM_THREADS=1 \
  -e MKL_NUM_THREADS=1 \
  -v "$PWD/artifacts/v1.168-max/maxserve_cta_extension:/workspace/artifacts/v1.168-max/maxserve_cta_extension:ro" \
  --entrypoint /bin/sh \
  localhost/cta-max-faiss:local \
  -c 'cd /workspace/artifacts/v1.168-max && python3 -B -u cta_native_e2e_test.py' \
  > "$LOG" 2>&1

RC=$?
echo "NATIVE E2E EXIT CODE: $RC"
echo "=== IMPORTANT RESULTS ==="
grep -E 'PASS|FAIL|ERROR|Error|Exception|CTA NATIVE HTTP STATUS|CTA RESPONSE:|CTA NATIVE END-TO-END|Killed|Traceback' "$LOG" | tail -25 | cut -c1-220
