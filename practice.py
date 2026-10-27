cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

find /application1 -maxdepth 3 -type f \
  \( -name '*max*.log' -o -name '*cta*.log' \) \
  -print 2>/dev/null | head -30
