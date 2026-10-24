cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
--runroot /run/containers/storage run --rm \
--pull=never --network=host --memory=8g \
-v "$PWD:/workspace:Z" -w /workspace \
-e PYTHONPATH=/workspace/artifacts/v1.168-max:/workspace/artifacts/v1.168/core-artifact:/workspace/artifacts/v1.168-max/cta_max \
--entrypoint /opt/venv/bin/python \
localhost/cta-max-faiss:local \
-u /workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_launcher.py \
--devices cpu \
--model-path /workspace/artifacts/v1.168/config \
--port 8000
