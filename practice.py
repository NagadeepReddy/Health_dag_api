find /application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max \
     /tmp /vzhome/sajjna8 \
  -maxdepth 7 -type f \
  \( -iname '*baseline*.json' -o -iname '*parity*' \
     -o -iname '*response*.json' -o -iname '*prediction*.json' \) \
  2>/dev/null | head -60
