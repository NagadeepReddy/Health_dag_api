podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm --pull=never --network=none \
--entrypoint /bin/sh localhost/cta-max-faiss:local \
-c 'nl -ba /opt/venv/lib/python3.12/site-packages/max/serve/pipelines/model_worker.py | sed -n "110,185p"'
