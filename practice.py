find /application1/sajjna8/rt-pzaas-cta-offers-v1 \
  -type f \( -name '*.pt' -o -name '*.safetensors' -o -name '*.gguf' \) \
  -printf '%p | %s bytes\n' | head -30
