podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --network none --read-only \
  --memory 1g --pids-limit 32 \
  --tmpfs /tmp:rw,size=256m \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -B -c 'import faiss; print("FAISS AVAILABLE: PASS"); print("FAISS PATH:", faiss.__file__)'
