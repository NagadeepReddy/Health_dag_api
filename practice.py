podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm --pull=never --network=none \
--entrypoint /bin/sh localhost/cta-max-faiss:local \
-c 'grep -n -E "model_config|resolve|weight|def __post_init__" /opt/venv/lib/python3.12/site-packages/max/pipelines/lib/config.py | tail -65'
