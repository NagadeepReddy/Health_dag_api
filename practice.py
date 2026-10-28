cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
timeout 20s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --network=none --read-only \
  --memory=256m --pids-limit=32 \
  --workdir /workspace \
  -v "$PWD":/workspace:ro \
  --entrypoint /bin/sh \
  localhost/cta-max-faiss:local \
  -c 'pwd; ls -lh artifacts/v1.168-max/cta_max/sequence_weights/fn_norm1_g.npy; echo "WEIGHT PATH CHECK: PASS"'
