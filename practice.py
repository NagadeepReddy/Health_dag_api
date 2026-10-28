cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
if [ "$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)" -lt 12582912 ]; then
  echo "STOP: insufficient available RAM"
else
  timeout -k 10s 160s podman \
    --root /application1/podman/storage \
    --runroot /run/containers/storage \
    run --rm --pull=never \
    --network=none --read-only --log-driver=none \
    --cpus=2 --pids-limit=64 --memory=8g \
    --tmpfs /tmp:rw,size=256m,mode=1777 \
    --tmpfs /root/.cache:rw,size=128m \
    --tmpfs /opt/venv/lib/python3.12/site-packages/max/_core_mojo/__mojocache__:rw,size=256m \
    -v "$PWD":/workspace:ro \
    -e PYTHONPATH=/workspace/artifacts/v1.168-max \
    -e PYTHONDONTWRITEBYTECODE=1 \
    -e OMP_NUM_THREADS=1 \
    -e MKL_NUM_THREADS=1 \
    -e OPENBLAS_NUM_THREADS=1 \
    -e TOKENIZERS_PARALLELISM=false \
    --entrypoint /opt/venv/bin/python3 \
    localhost/cta-max-faiss:local -B \
    /workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_e2e_test.py \
    > /application1/cta_queue_fix_e2e.log 2>&1

  rc=$?
  echo "TEST EXIT CODE: $rc"
  grep -E 'CTA RESPONSE QUEUE SEND|CTA HTTP QUEUE ITEM|CTA NATIVE HTTP STATUS|CTA RESPONSE:|CTA NATIVE END-TO-END|Traceback|Error|Exception' \
    /application1/cta_queue_fix_e2e.log | tail -25 || true
fi
