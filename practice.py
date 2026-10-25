echo "=== CONTAINER STATUS ==="
podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  ps -a --filter name=cta-native-live

echo "=== SERVER EVENTS ==="
podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  logs cta-native-live 2>&1 | \
  grep -Ei 'startup complete|CTA REQUEST RECEIVED|LIVE RESPONSE ID|LIVE DISPATCH MATCH|CTA HTTP BRIDGE|CTA HTTP QUEUE ITEM|traceback|exception|error|POST /v2/cta/predict' | tail -30
