cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  ps -a --format "ID={{.ID}} STATUS={{.Status}} NAME={{.Names}}"
