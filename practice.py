
podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  logs --tail 250 cta-batch2-trace-8766-10g 2>&1 \
  | tail -100
