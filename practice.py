cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
set -o pipefail && \
timeout -s TERM -k 5s 40s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --memory=6g --memory-swap=6g \
  --cpus=2 --pids-limit=64 \
  --network=none --read-only --log-driver=none \
  --tmpfs /tmp:rw,size=512m,mode=1777 \
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
  2>&1 | grep --line-buffered -E \
  'CTA MODEL LOAD|CTA PREDICT_RAW|CTA preprocess|CTA postprocess|Traceback|Error|Exception|File "|CTA STATUS|CTA RESPONSE:|NATIVE CTA JSON E2E|Timeout|Terminated|Killed'
