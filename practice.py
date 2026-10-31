REPO=/application1/sajjna8/rt-pzaas-cta-offers-v1

echo "=== TRITON MODEL CONFIG ==="
git -C "$REPO" show \
  triton:artifacts/v1.168-triton/config.pbtxt |
  head -120

echo "=== TRITON INFERENCE IMPLEMENTATION ==="
git -C "$REPO" show \
  triton:artifacts/v1.168-triton/1/model.py |
  head -200
