REPO=/application1/sajjna8/rt-pzaas-cta-offers-v1

echo "=== TRITON SERVING CODE CHANGES ==="

git -C "$REPO" diff --stat \
  triton origin/triton -- \
  artifacts/baseImage/Dockerfile.triton \
  artifacts/v1.168-triton/config.pbtxt \
  artifacts/v1.168-triton/1/model.py \
  artifacts/v1.168-triton/test_triton_client.py

echo "=== ACTUAL CODE DIFFERENCES ==="

git -C "$REPO" diff --unified=2 \
  triton origin/triton -- \
  artifacts/v1.168-triton/config.pbtxt \
  artifacts/v1.168-triton/1/model.py |
head -100
