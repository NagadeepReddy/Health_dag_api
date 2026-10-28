cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
echo "=== ACTUAL SEQUENCE WEIGHTS ===" && \
ls -lah artifacts/v1.168-max/cta_max/sequence_weights/ && \
echo "=== WEIGHT FILE COUNT ===" && \
find artifacts/v1.168-max/cta_max/sequence_weights \
  -maxdepth 1 -type f -name '*.npy' | wc -l
