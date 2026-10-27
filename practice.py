(
  NAME=cta-max-test-$$
  P="podman --root /application1/podman/storage --runroot /run/containers/storage"

  cleanup() {
    $P stop --time 5 "$NAME" >/dev/null 2>&1 || true
  }
  trap cleanup EXIT INT TERM

  timeout -s TERM -k 10s 45s $P run \
    --name "$NAME" --rm --pull=never \
    --memory=4g --cpus=2 --pids-limit=128 \
    --network=none --read-only --log-driver=none \
    --tmpfs /tmp:rw,size=256m \
    --tmpfs /root:rw,size=64m \
    -v /application1/sajjna8/rt-pzaas-cta-offers-v1:/workspace:ro \
    -e PYTHONPATH=/workspace/artifacts/v1.168-max \
    -e PYTHONDONTWRITEBYTECODE=1 \
    -e PYTHONUNBUFFERED=1 \
    -e HOME=/tmp -e TMPDIR=/tmp \
    -e XDG_CACHE_HOME=/tmp/cache \
    -e HF_HOME=/tmp/hf \
    -e MODULAR_HOME=/tmp/modular \
    --entrypoint /opt/venv/bin/python \
    localhost/cta-max-faiss:local \
    /workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_launcher.py \
    --model-path /workspace/artifacts/v1.168-max/cta_native_model

  echo "MAX test exit code: $?"
)
