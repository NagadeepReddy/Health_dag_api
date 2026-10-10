podman run --rm \
-v "$PWD:/workspace" \
-w /workspace \
--entrypoint python \
docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
-c "from max.driver import Tensor; import inspect; print([x for x in dir(Tensor) if any(k in x.lower() for k in ['numpy','dlpack','copy','host','item'])])"
