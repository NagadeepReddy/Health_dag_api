find /application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max -maxdepth 3 -type f \( -name '*.pt' -o -name '*.safetensors' -o -name '*.onnx' \) -printf '%p %s bytes\n' | head -20
