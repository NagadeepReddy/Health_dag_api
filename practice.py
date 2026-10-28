cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
find artifacts/v1.168 artifacts/v1.168-max \
  -maxdepth 5 -type f \
  \( -iname '*sanity*.json' -o -iname '*adjust*.json' -o -iname '*e2e*.json' \) \
  -print
