podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  inspect cta-postman-validated-20261030 \
  --format 'MEMORY={{.HostConfig.Memory}} SHM={{.HostConfig.ShmSize}} PIDS={{.HostConfig.PidsLimit}} NETWORK={{.HostConfig.NetworkMode}} STATUS={{.State.Status}}'
