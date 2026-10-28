cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

name=cta_env_e2e_1028
log=/application1/cta_env_e2e_1028.log

pdm() {
  podman --root /application1/podman/storage \
         --runroot /run/containers/storage "$@"
}

cleanup() {
  pdm stop --time 5 "$name" >/dev/null 2>&1 || true
  pdm rm -f "$name" >/dev/null 2>&1 || true
}

if pdm container exists "$name" || [ -e "$log" ]; then
  echo "STOP: test container or log already exists"
elif [ "$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)" -lt 16777216 ]; then
  echo "STOP: available RAM below 16 GiB"
elif [ "$(df -Pk /application1 | awk 'NR==2 {print $4}')" -lt 10485760 ]; then
  echo "STOP: application1 disk space below 10 GiB"
else
  trap cleanup EXIT

  timeout -s TERM -k 10s 180s \
  podman \
    --root /application1/podman/storage \
    --runroot /run/containers/storage \
    run --name "$name" --rm --pull=never \
    --workdir /workspace \
    --memory=8g --memory-swap=8g \
    --cpus=2 --pids-limit=64 \
    --network=none --read-only --log-driver=none \
    --tmpfs /tmp:rw,size=256m,mode=1777 \
    --tmpfs /root/.cache:rw,size=128m,mode=1777 \
    --tmpfs /opt/venv/lib/python3.12/site-packages/max/_core_mojo/__mojocache__:rw,size=256m,mode=1777 \
    -v /application1/sajjna8/rt-pzaas-cta-offers-v1:/workspace:ro \
    -e modelId=rt-pzaas-cta-offers-v1 \
    -e expThrottleLabel=T \
    -e PYTHONPATH=/workspace:/workspace/artifacts/v1.168-max \
    -e PYTHONDONTWRITEBYTECODE=1 \
    -e PYTHONUNBUFFERED=1 \
    -e OMP_NUM_THREADS=1 \
    -e MKL_NUM_THREADS=1 \
    -e OPENBLAS_NUM_THREADS=1 \
    -e TOKENIZERS_PARALLELISM=false \
    --entrypoint /opt/venv/bin/python3 \
    localhost/cta-max-faiss:local \
    -B /workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_e2e_test.py \
    > "$log" 2>&1

  rc=$?
  cleanup
  trap - EXIT

  echo "TEST EXIT CODE: $rc"
  echo "=== IMPORTANT RESULTS ==="
  grep -E 'MAX INFERENCE EXECUTED|CTA postprocess|CTA PREDICT_RAW|CTA RESPONSE|CTA STATUS|KeyError|Exception|Error|Timeout|PASS' "$log" | tail -30
  echo "=== LAST OUTPUT ==="
  tail -20 "$log"
fi
