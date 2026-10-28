cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
timeout -k 5s 35s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --memory=2g --cpus=1 --pids-limit=64 \
  --network=none --read-only --log-driver=none \
  --tmpfs /tmp:rw,nosuid,size=128m,mode=1777 \
  --tmpfs /opt/venv/lib/python3.12/site-packages/max/_core_mojo/__mojocache__:rw,nosuid,size=256m \
  -e HOME=/tmp \
  -e TMPDIR=/tmp \
  -e PYTHONDONTWRITEBYTECODE=1 \
  --entrypoint /opt/venv/bin/python3 \
  localhost/cta-max-faiss:local \
  -B -c 'import max._core_mojo; print("MOJO CACHE FIX: PASS", flush=True)'
