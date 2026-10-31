echo "=== TRITON PROJECT FILES ==="

find /application1 /application /home -maxdepth 7 \
  \( -type d \( \
    -name site-packages -o \
    -name .cache -o \
    -name podman -o \
    -name __pycache__ -o \
    -name 'CTA_MAX_*' \
  \) \) -prune -o \
  \( -iname '*triton*' -o \
     -name config.pbtxt -o \
     -iname '*model_repository*' \) \
  -print 2>/dev/null | head -60

echo "=== TRITON CONTAINERS ==="

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  ps -a --format '{{.Names}} {{.Image}}' |
  grep -Ei 'triton|sriram' || true
