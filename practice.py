set -o pipefail

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  cp cta-postman-validated-20261030:/tmp/cta_postman_native.log - \
  | tar -xOf - \
  | grep -nEi 'traceback|exception|error|worker|spawn|failed|timeout|model load|ready|shutdown' \
  | head -80
