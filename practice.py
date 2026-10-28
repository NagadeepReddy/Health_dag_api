podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --memory=512m --cpus=1 --pids-limit=64 \
  --network=none --read-only --log-driver=none \
  --entrypoint /bin/grep \
  localhost/cta-max-faiss:local \
  -Rn -C 4 -E 'response_worker\(|def _enter_|def __aenter__' \
  /opt/venv/lib/python3.12/site-packages/max/serve/api_server.py \
  /opt/venv/lib/python3.12/site-packages/max/serve/pipelines
