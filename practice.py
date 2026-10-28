podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --memory=512m --cpus=1 --pids-limit=64 \
  --network=none --read-only --log-driver=none \
  --entrypoint /bin/grep \
  localhost/cta-max-faiss:local \
  -Rn -A 65 '^class PipelineArchitecture' \
  /opt/venv/lib/python3.12/site-packages/max/pipelines/lib
