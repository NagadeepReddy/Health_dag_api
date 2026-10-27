cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1
find artifacts/v1.168-max/maxserve_cta_extension \
  -maxdepth 1 -type f -name '*.py' -print | sort
