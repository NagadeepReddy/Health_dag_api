cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

find artifacts/v1.168 -maxdepth 5 -type f \
  \( -iname '*requirements*' -o -iname 'pyproject.toml' \
     -o -iname '*environment*.yml' -o -iname 'Dockerfile*' \) \
  -print
