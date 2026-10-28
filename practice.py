cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
find artifacts/v1.168/core-artifact -maxdepth 3 -type f -name '*.pt' -printf '%s %p\n' | sort -nr | head -15
