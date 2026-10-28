cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

name=cta_native_corrected_1028
log=/application1/cta_native_corrected_1028.log

pdm() {
  podman --root /application1/podman/storage \
         --runroot /run/containers/storage "$@"
}

if [ ! -f artifacts/v1.168-max/maxserve_cta_extension/cta_native_e2e_test.py ]; then
  echo "STOP: Native test script missing"
elif [ ! -f artifacts/v1.168-max/cta_native_adjusted_sanity_input.json ]; then
  echo "STOP: Adjusted JSON missing"
elif pdm container exists "$name" || [ -e "$log" ]; then
  echo "STOP: Test container or log already exists"
elif [ "$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)" -lt 16777216 ]; then
  echo "STOP: Available RAM below 16 GiB"
else
  timeout -s TERM -k 10s 210s \
  podman \
    --root /application1/podman/storage \
    --runroot /run/containers/storage \
    run --name "$name" --rm --pull=never \
    --workdir /workspace \
    --network=none --read-only --log-driver=none \
    --memory=8g --memory-swap=8g \
    --cpus=2 --pids-limit=64 \
    --tmpfs /tmp:rw,size=256m,mode=1777 \
    --tmpfs /root/.cache:rw,size=128m,mode=1777 \
    --tmpfs /opt/venv/lib/python3.12/site-packages/max/_core_mojo/__mojocache__:rw,size=256m,mode=1777 \
    -v "$PWD":/workspace:ro \
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

  if pdm inspect "$name" --format '{{json .Config.Cmd}}' 2>/dev/null \
     | grep -Fq 'cta_native_e2e_test.py'; then
    pdm stop --time 5 "$name" >/dev/null 2>&1 || true
  fi

  echo "TEST EXIT CODE: $rc"
  echo "=== IMPORTANT RESULTS ==="
  grep -E 'CTA MODEL LOAD|MAX INFERENCE EXECUTED|CTA postprocess|CTA RESPONSE QUEUE SEND|CTA HTTP QUEUE ITEM|CTA NATIVE HTTP STATUS|CTA RESPONSE:|PASS|Traceback|Exception|Error' \
    "$log" | tail -35

  echo "=== LAST LOGS ==="
  tail -15 "$log"
fi
