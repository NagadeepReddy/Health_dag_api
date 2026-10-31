REPO=/application1/sajjna8/rt-pzaas-cta-offers-v1
STAGE=/application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031

echo "=== GIT BRANCH ==="
git -C "$REPO" branch --show-current

echo "=== ESSENTIAL FILES FOR GIT ==="

for REL in \
  run_cta_native.sh \
  artifacts/v1.168-max/real_max_batch2_backend.py \
  artifacts/v1.168-max/cta_native_batch2_release_candidate/maxserve_cta_extension/cta_native_launcher.py \
  artifacts/v1.168-max/cta_native_batch2_release_candidate/maxserve_cta_extension/cta_worker_adapter.py
do
  if [ -f "$STAGE/$REL" ]; then
    echo "HANDOFF: PASS $REL"
  else
    echo "HANDOFF: MISSING $REL"
  fi

  if git -C "$REPO" ls-files --error-unmatch "$REL" >/dev/null 2>&1; then
    echo "GIT: TRACKED"
  else
    echo "GIT: NOT TRACKED"
  fi
done

echo "GIT HANDOFF READINESS CHECK COMPLETE"
