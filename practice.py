cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1
echo "=== BRANCH ==="
git branch --show-current
echo "=== CHANGED FILES ==="
git status --short --untracked-files=normal -- artifacts/v1.168-max
echo "=== REMOTE ==="
git remote -v
