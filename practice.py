find /mnt/cta-recovery /application1 \
  -path '*/podman/storage' -prune -o \
  -type f -name 'faiss_cpu-1.15.1-*.whl' -print \
  2>/dev/null | head -5
