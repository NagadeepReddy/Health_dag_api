ROOT=/application1/sajjna8/rt-pzai-bplan-v1

echo "=== CHECK VZHOME FOR ORIGINAL LOOKUP ==="
find /vzhome -type f -name 'page_seq_2.csv' -print 2>/dev/null

echo "=== BPLAN ARTIFACT STORAGE REFERENCES ==="
grep -RnI -iE \
  'page_seq_2|gs://|s3://|artifactory|artifact.uri|artifact_path|lookup.path' \
  "$ROOT" \
  --include='*.yaml' --include='*.yml' \
  --include='*.json' --include='*.md' \
  --include='*.py' --include='*.sh' \
  2>/dev/null | head -45

echo "=== GIT LFS ARTIFACTS ==="
git -C "$ROOT" lfs ls-files 2>/dev/null | head -25 || true
