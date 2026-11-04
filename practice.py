cd /application1/sajjna8/rt-pzaas-v1.0 && {
  echo "=== RUNNING CONTAINERS ==="
  podman ps --format 'NAME={{.Names}} IMAGE={{.Image}} STATUS={{.Status}}'
  echo "=== AVAILABLE PYTORCH/MAX IMAGES ==="
  podman images --format '{{.Repository}}:{{.Tag}}' | grep -Ei 'torch|pytorch|max|pzaas|cta' || true
  echo "=== SAVED REFERENCE FILES ==="
  find artifacts/v1.472-max/pzaas_max/validation -maxdepth 2 -type f \( -name '*.pt' -o -name '*reference*.py' \) -print
  echo "ORIGINAL DS: UNCHANGED"
}
