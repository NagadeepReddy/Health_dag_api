grep -RniE 'class .*Pool|ihq_pooling[[:space:]]*=|jet_pooling[[:space:]]*=' \
  artifacts/v1.168/utils \
  --include='*.py' | head -35
