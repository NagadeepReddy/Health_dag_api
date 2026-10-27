podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --memory=512m --cpus=1 --pids-limit=64 \
  --network=none --read-only \
  --entrypoint /bin/grep \
  localhost/cta-max-faiss:local \
  -n -A 45 'def _validate_final_architecture_model_path_weight_path' \
  /opt/venv/lib/python3.12/site-packages/max/pipelines/lib/model_config.py
