find /application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168 \
  -mindepth 1 -maxdepth 2 \
  \( -type d -o -type f \) \
  ! -name '__pycache__' \
  -printf '%y %P\n' | sort
