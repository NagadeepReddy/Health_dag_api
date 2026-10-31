REPO=/application1/sajjna8/rt-pzaas-cta-offers-v1

echo "=== LOCAL TRITON COMMIT ==="
git -C "$REPO" log -1 \
  --format='%h | %an | %ad | %s' \
  --date=short triton

echo "=== TRACKED REMOTE COMMIT ==="
git -C "$REPO" log -1 \
  --format='%h | %an | %ad | %s' \
  --date=short origin/triton

echo "=== ACTUAL REMOTE BRANCH ==="
timeout 15 git -C "$REPO" \
  ls-remote --heads origin triton || true

echo "=== RECENT TRITON HISTORY ==="
git -C "$REPO" log -5 \
  --format='%h | %an | %ad | %s' \
  --date=short triton

echo "=== TRITON FILE SUMMARY ==="
git -C "$REPO" ls-tree -r --name-only triton |
grep -E 'Dockerfile.triton|config.pbtxt|/model.py$|test_triton_client.py|deployment-params.json'

echo "READ-ONLY INSPECTION: COMPLETE"
