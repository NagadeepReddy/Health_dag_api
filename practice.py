STAGE=/application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031

echo "=== BACKEND CODE DIFFERENCES ==="
diff -u \
 "$STAGE/artifacts/v1.168-max/real_max_batch2_backend.py" \
 "$STAGE/batch2/real_max_batch2_backend.py" |
 head -100

echo "=== BACKEND DEPENDENCIES ==="
grep -RIn \
 --include='*.py' --include='*.sh' \
 'real_max_batch2_backend' "$STAGE" |
 head -50

echo "BACKEND AUDIT COMPLETE"
