REPO=/application1/sajjna8/rt-pzaas-cta-offers-v1

echo "=== TRITON FILE REMOVAL HISTORY ==="
git -C "$REPO" log --all --oneline \
  --diff-filter=D -- \
  artifacts/v1.168-triton/1/model.py \
  artifacts/v1.168-triton/config.pbtxt \
  artifacts/v1.168-triton/test_triton_client.py |
head -20

echo "=== LATEST PATCH SUMMARY ==="
git -C "$REPO" show --format=fuller \
  --summary --stat origin/triton |
head -70

echo "=== CURRENT BRANCH ==="
git -C "$REPO" branch --show-current
