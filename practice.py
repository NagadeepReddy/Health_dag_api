echo "=== HOST MEMORY ==="
free -h

echo "=== CONTAINER MEMORY USAGE ==="
podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  stats --no-stream \
  --format 'NAME={{.Name}} MEMORY={{.MemUsage}} CPU={{.CPU}}'
