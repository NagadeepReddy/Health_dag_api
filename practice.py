podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  inspect sharp_gates \
  --format '{{json .Config.Cmd}}' \
  | grep -Fq 'cta_native_e2e_test.py' && \
podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  stop --time 10 sharp_gates
