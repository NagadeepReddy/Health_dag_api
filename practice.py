cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

f=artifacts/v1.168-max/maxserve_cta_extension/cta_architecture_registration.py

sed -i 's/supported_encodings={SupportedEncoding.float32},/supported_encodings={SupportedEncoding.float32: llama_arch.supported_encodings[SupportedEncoding.bfloat16]},/' "$f"

grep -nE 'default_encoding|supported_encodings' "$f"
