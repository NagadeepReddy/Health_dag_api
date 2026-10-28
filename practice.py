cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
timeout -k 5s 120s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --memory=4g --cpus=1 --pids-limit=128 \
  --network=none --read-only --log-driver=none \
  --tmpfs /tmp:rw,nosuid,size=128m,mode=1777 \
  --tmpfs /opt/venv/lib/python3.12/site-packages/max/_core_mojo/__mojocache__:rw,nosuid,size=256m \
  -e HOME=/tmp \
  -e TMPDIR=/tmp \
  -e XDG_CACHE_HOME=/tmp/cache \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e PYTHONPATH=/workspace:/workspace/artifacts/v1.168-max \
  -e OMP_NUM_THREADS=1 \
  -e MKL_NUM_THREADS=1 \
  -e OPENBLAS_NUM_THREADS=1 \
  -e NUMEXPR_NUM_THREADS=1 \
  -e BLIS_NUM_THREADS=1 \
  -v "$PWD":/workspace:ro \
  -w /workspace \
  --entrypoint /opt/venv/bin/python3 \
  localhost/cta-max-faiss:local \
  -B artifacts/v1.168-max/maxserve_cta_extension/cta_native_e2e_test.py
