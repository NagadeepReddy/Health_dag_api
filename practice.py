cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
find artifacts/v1.168-max \
  -type f \( -name '*.safetensors' -o -name '*.gguf' \) \
  -printf '%p\n' | head -30
