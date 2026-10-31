REPO=/application1/sajjna8/rt-pzaas-cta-offers-v1

echo "=== REMOTE TRITON SERVING FILES ==="
git -C "$REPO" ls-tree -r --name-only origin/triton |
grep -E 'config.pbtxt$|/model.py$|Dockerfile.triton$|test_triton_client.py$' |
head -30

echo "=== TRITON TEST OR DEPLOYMENT LOGS ==="
find /application1 -maxdepth 5 -type f \
  \( -iname '*triton*.log' -o \
     -iname '*triton*result*' -o \
     -iname '*triton*report*' \) \
  -print 2>/dev/null | head -30

echo "TRITON EVIDENCE CHECK COMPLETE"
