REPO=/application1/sajjna8/rt-pzaas-cta-offers-v1

echo "=== COMMITS ON TRACKED REMOTE ==="
git -C "$REPO" log --oneline \
  triton..origin/triton | head -20

echo "=== TRITON CODE DIFFERENCES ==="
git -C "$REPO" diff --stat \
  triton origin/triton -- \
  artifacts/v1.168-triton \
  artifacts/baseImage/Dockerfile.triton

echo "=== LATEST TRITON PATCH ==="
git -C "$REPO" show --stat --oneline \
  origin/triton | head -60

echo "TRITON COMPARISON: COMPLETE"
