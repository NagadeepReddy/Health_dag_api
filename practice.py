podman run --rm \
--entrypoint python \
docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
-c "from max.graph import ops; print('where:',hasattr(ops,'where')); print('constant:',hasattr(ops,'constant')); print('broadcast_to:',hasattr(ops,'broadcast_to'))"
