podman run --rm \
-v "$PWD:/workspace" -w /workspace \
--entrypoint python \
docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
artifacts/v1.168-max/cta_max/run_transformer_max.py
