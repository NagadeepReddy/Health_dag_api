cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

grep -RniE --include='*requirements*.txt' \
  'faiss|numpy|torch' artifacts/v1.168 | head -30
