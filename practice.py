if [ "$(id -u)" -eq 0 ]; then
  podman --root /application1/podman/storage \
    --runroot /run/containers/storage \
    ps -a --format '{{.Names}} | {{.Status}}'
else
  echo "STOP: Return to the previous root@10-119-98-21 terminal. Do not use sudo."
fi
