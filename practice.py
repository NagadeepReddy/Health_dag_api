REPO=/application1/sajjna8/rt-pzaas-cta-offers-v1

echo "=== TRITON TEST CLIENT ==="
git -C "$REPO" show \
  triton:artifacts/v1.168-triton/test_triton_client.py |
  head -180

echo "=== TRITON DEPLOYMENT FILES ==="
git -C "$REPO" ls-tree -r --name-only triton |
grep -Ei 'triton.*(readme|deploy|test|client)|helm|kserve|values.yaml' |
head -60
