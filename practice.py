find /application1/sajjna8/rt-pzaas-cta-offers-v1 \
  -type f \( -name 'config.pbtxt' -o -name 'model.py' \
  -o -name 'Dockerfile.triton' \) -print | head -30
