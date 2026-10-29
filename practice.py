cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

CANDIDATE=/application1/cta_max_native_release_candidate_20261028
LOG=/application1/cta_max_true_batch_dev_20261028/native_concurrent2_allweights.log

echo "=== NATIVE TIMEOUT SETTINGS ==="
grep -RniE 'timeout|wait_for|deadline|HTTP_504|status_code=504|120' \
  "$CANDIDATE" \
  --include='*.py' | head -45

echo "=== SECOND REQUEST FAILURE ==="
grep -niE 'timeout|timed out|504|cancel|queue|deadline' \
  "$LOG" | tail -35

echo "CHECK COMPLETE — NO FILES MODIFIED"
