unshare -m --propagation private sh -c '
podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  images --format "{{.Repository}}:{{.Tag}}" |
grep "modular/max-full:latest"
'
