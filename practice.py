cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
grep -Rn -C 4 --include='*.py' \
  -E "(\['modelId'\]|\[\"modelId\"\]|\.get\(['\"]modelId|modelId)" \
  pipeline.py artifacts/v1.168-max/maxserve_cta_extension/ \
  | head -100
