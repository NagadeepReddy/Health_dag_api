podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  stats --no-stream \
  --format 'NAME={{.Name}} MEM={{.MemUsage}} MEM%={{.MemPerc}} CPU%={{.CPU}}'
