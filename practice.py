cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
timeout 15s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --network=none --read-only \
  --memory=128m --pids-limit=16 \
  -v "$PWD/artifacts/v1.168-max/maxserve_cta_extension:/workspace/artifacts/v1.168-max/maxserve_cta_extension:ro" \
  --entrypoint /bin/sh \
  localhost/cta-max-faiss:local \
  -c 'grep -n "os.environ.setdefault" /workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_spawn_worker.py && echo "CONTAINER ENV FIX: VISIBLE"'
