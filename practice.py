REPO=/application1/sajjna8/rt-pzaas-cta-offers-v1
STAGE=/application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031

echo "=== GIT STAGED MAX FILES ==="
git -C "$REPO" diff --cached --name-status -- artifacts/v1.168-max

echo "=== HANDOFF PYTHON AND LAUNCHER FILES ==="
find "$STAGE" -type f \
  \( -name '*.py' -o -name '*.sh' \) \
  -printf '%P\n' | sort

echo "=== POSSIBLE INVESTIGATION FILES ==="
find "$STAGE" -type f \
  \( -iname '*test*' -o -iname '*debug*' \
  -o -iname '*backup*' -o -iname '*.bak' \
  -o -iname '*sanity*' \) \
  -printf '%P\n' | head -60
