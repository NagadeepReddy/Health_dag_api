
cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
find artifacts/v1.168-max/maxserve_cta_extension \
-maxdepth 1 -type f \
\( -iname '*factory*.py' -o -iname '*model*.py' -o -iname '*config*.py' \) \
-print
