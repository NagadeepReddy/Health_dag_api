podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --memory=512m --cpus=1 --pids-limit=64 \
  --network=none --read-only \
  --entrypoint /bin/grep \
  localhost/cta-max-faiss:local \
  -nE 'class PipelineConfig|model_validator|model_post_init|def __init__|_validate_and_resolve_remaining_pipeline_config' \
  /opt/venv/lib/python3.12/site-packages/max/pipelines/lib/config.py
