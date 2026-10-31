REPO=/application1/sajjna8/rt-pzaas-cta-offers-v1

echo "=== TRITON BRANCH ==="
git -C "$REPO" branch -a | grep -i triton || true

echo "=== TRITON IMPLEMENTATION FILES ==="
git -C "$REPO" ls-tree -r --name-only triton 2>/dev/null |
grep -Ei 'triton|config.pbtxt|model_repository|backend|server|docker' |
head -60

echo "TRITON INSPECTION COMPLETE"
