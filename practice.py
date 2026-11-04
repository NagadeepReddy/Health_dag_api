cd /application1/sajjna8/rt-pzaas-v1.0 && \
mkdir -p artifacts/v1.472-max/pzaas_max/validation/python_deps && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm --pull=never \
--network host --memory 2g \
-v "$PWD/artifacts/v1.472-max/pzaas_max/validation/python_deps:/deps:rw" \
--entrypoint /opt/venv/bin/python \
localhost/cta-max-faiss:local \
-m pip install --disable-pip-version-check \
--no-cache-dir --retries 0 --timeout 8 \
--target /deps "einops==0.8.1" && \
echo "PZAAS REAL EINOPS: INSTALLED" || \
echo "NETWORK BLOCKED: APPROVED OFFLINE WHEEL REQUIRED"
