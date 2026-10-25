podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  logs cta-native-live 2>&1 | \
  grep -Ei 'CTA REQUEST RECEIVED|CTA NATIVE RESPONSE|CTA WORKER RESPONSE IDS: \[RequestID|CTA MAX REQUEST|CTA SOCKET|Traceback|Exception|Error|Failed to put|POST /v2/cta/predict' | \
  grep -v 'RESPONSE IDS: \[\]' | tail -35
