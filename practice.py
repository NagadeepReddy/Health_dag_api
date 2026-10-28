cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
printf 'EXPECTED FILE:\n' && \
ls -l artifacts/v1.168-max/cta_max/sequence_weights/fn_norm1_g.npy 2>&1 || true
find /application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts \
  -type f -name 'fn_norm1_g.npy' -print
