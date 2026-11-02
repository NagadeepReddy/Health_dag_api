echo "=== HOST PARITY FILES ==="
find /application1 /bplan_out -type f \
  \( -name 'bplan_neural_inputs.pt' -o \
     -name 'bplan_pytorch_neural_output.pt' \) \
  -print 2>/dev/null

echo "=== EXISTING CONTAINERS ==="
podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  ps -a --format '{{.Names}} | {{.Status}}'
