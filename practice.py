cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
timeout -k 5s 90s podman \
--root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm --pull=never \
-p 127.0.0.1:8000:8000 \
-v "$PWD:/workspace:ro" \
-w /workspace \
-e PYTHONPATH=/workspace/artifacts/v1.168-max \
--entrypoint /opt/venv/bin/python \
localhost/cta-max-faiss:local \
-m maxserve_cta_extension.cta_native_launcher \
--model-path /workspace/artifacts/v1.168-max/cta_native_model \
--custom-architectures cta_native_model \
--quantization-encoding float32 \
--port 8000
