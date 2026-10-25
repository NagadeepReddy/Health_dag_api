podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm --pull=never --network=none \
--entrypoint /bin/sh localhost/cta-max-faiss:local \
-c 'sed -n "390,445p" /opt/venv/lib/python3.12/site-packages/max/pipelines/lib/registry.py'
