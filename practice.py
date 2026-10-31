REPO=/application1/sajjna8/rt-pzaas-cta-offers-v1
STAGE=/application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031

echo "=== CURRENT GIT BRANCH ==="
git -C "$REPO" branch --show-current

echo "=== EXISTING CHANGES ==="
git -C "$REPO" status --short --untracked-files=no

echo "=== CLEAN HANDOFF CONTENTS ==="
find "$STAGE" -mindepth 1 -maxdepth 2 \
  -printf '%y %P\n' | head -80

echo "=== PACKAGE SIZE BREAKDOWN ==="
du -sh "$STAGE"/* 2>/dev/null | sort -h

echo "=== EXISTING MAX FILES IN GIT ==="
git -C "$REPO" ls-files 'artifacts/v1.168-max/*' | head -40
