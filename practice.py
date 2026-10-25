cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
grep -RInE '"(quantization|quantization_config|weight_path|weight_format|model_path|architectures|model_type)"|q4_k|gguf' \
artifacts/v1.168-max/cta_native_model \
artifacts/v1.168-max/maxserve_cta_extension/cta_architecture* \
2>/dev/null | head -45
