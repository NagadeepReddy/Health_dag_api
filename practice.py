cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

grep -RnEi --include='*.py' '\bfaiss\b' \
  artifacts/v1.168/core-artifact | head -35
