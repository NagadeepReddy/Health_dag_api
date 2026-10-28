cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

name=cta_final_diag_1028
log=/application1/cta_final_diag_1028.log

pdm() {
  podman --root /application1/podman/storage \
         --runroot /run/containers/storage "$@"
}

if pdm container exists "$name"; then
  echo "STOP: diagnostic container name already exists"
else
  avail=$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)
  disk=$(df -Pk /application1 | awk 'NR==2 {print $4}')

  if [ "$avail" -lt 12582912 ] || [ "$disk" -lt 10485760 ]; then
    echo "STOP: insufficient RAM or application1 disk space"
  else
    timeout -s TERM -k 5s 75s \
    podman \
      --root /application1/podman/storage \
      --runroot /run/containers/storage \
      run --name "$name" --rm --pull=never \
      --workdir /workspace \
      --memory=6g --memory-swap=6g \
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

    rc=$?
    echo "TEST EXIT CODE: $rc"

    pdm stop --time 5 "$name" >/dev/null 2>&1 || true

    echo "=== LAST DIAGNOSTIC OUTPUT ==="
    tail -80 "$log"
  fi
fi
