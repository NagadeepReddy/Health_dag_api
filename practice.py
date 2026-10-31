podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  logs --timestamps --since 10m \
  --tail 250 cta-clean-native-batch2 2>&1 |
  grep -A 35 -B 5 -E \
  'CTA PREDICT EXCEPTION|FileNotFoundError|CTA RESPONSE WORKER|Traceback' |
  tail -100
