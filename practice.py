podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  logs --timestamps --since 15m \
  cta-clean-native-batch2 2>&1 |
  grep -E 'CTA PREDICT|FileNotFoundError|seq_dense_weight|Timeout|Error|Exception' |
  tail -35
