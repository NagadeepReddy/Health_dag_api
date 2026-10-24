podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm --pull=never --network=none \
--entrypoint /bin/sh localhost/cta-max-faiss:local \
-c "sed -n '90,125p;180,230p' /opt/venv/lib/python3.12/site-packages/max/pipelines/lib/registry.py"
