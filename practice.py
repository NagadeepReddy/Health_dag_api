cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
timeout 15s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --network=none --read-only \
  --memory=128m --pids-limit=16 \
  --entrypoint /bin/true \
  localhost/cta-max-faiss:local

echo "OCI TEST EXIT CODE: $?"
