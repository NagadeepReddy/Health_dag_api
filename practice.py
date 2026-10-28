cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

name=cta_memfix_test_1028
log=/application1/cta_memfix_test_1028.log

pdm() {
  podman --root /application1/podman/storage \
         --runroot /run/containers/storage "$@"
}

if pdm container exists "$name" || [ -e "$log" ]; then
  echo "STOP: test container or log already exists"
else
  ram=$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)
  disk=$(df -Pk /application1 | awk 'NR==2 {print $4}')

  if [ "$ram" -lt 16777216 ] || [ "$disk" -lt 10485760 ]; then
    echo "STOP: insufficient available RAM or disk"
  else
    timeout -s TERM -k 5s 95s \
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

    echo "TEST EXIT CODE: $?"

    if pdm inspect "$name" --format '{{json .Config.Cmd}}' 2>/dev/null \
      | grep -Fq 'cta_native_e2e_test.py'; then
      pdm stop --time 5 "$name"
    fi

    echo "=== IMPORTANT RESULTS ==="
    grep -E 'CTA MODEL LOAD|CTA preprocess|MAX INFERENCE|EXECUTING REAL|CTA STATUS|CTA RESPONSE|CTA PREDICT_RAW|Timeout|Exception|Error|Killed|PASS' "$log" | tail -35

    echo "=== LAST OUTPUT ==="
    tail -20 "$log"
  fi
fi
