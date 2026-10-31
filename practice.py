REPO=/application1/sajjna8/rt-pzaas-cta-offers-v1

echo "=== TRITON SERVING FILES ==="
git -C "$REPO" ls-tree -r --name-only triton |
grep -Ei 'config.pbtxt$|model.py$|Dockerfile.triton$|triton.*\.(py|sh)$|backend.*\.py$|server.*\.py$|launch.*\.sh$' |
head -60

echo "=== TRITON DOCKERFILE ==="
git -C "$REPO" show triton:artifacts/baseImage/Dockerfile.triton |
head -100
