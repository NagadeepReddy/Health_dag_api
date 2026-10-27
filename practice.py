podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --memory=512m --cpus=1 --pids-limit=64 \
  --network=none --read-only \
  --entrypoint /bin/cat \
  localhost/cta-max-faiss:local \
  /opt/venv/lib/python3.12/site-packages/max/pipelines/architectures/llama3_arch.py \
  | grep -A 20 -B 5 'supported_encodings'
