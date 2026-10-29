echo "=== CURRENT BACKEND ==="
sed -n '1,65p' /application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/real_max_batch2_backend.py

echo "=== EXISTING BATCH-2 CANDIDATE ==="
sed -n '1,85p' /application1/cta_max_true_batch_dev_20261028/batch2_candidate/cta_max/grecbase_fusion_full_head_72_max.py

echo "=== PREVIOUS SUCCESS ==="
grep -E 'REAL MAX BATCH-2: PASS|REAL INPUT CONTRACT: PASS|BATCH-2 OUTPUT|EXIT CODE' /application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/real_max_batch2_after_cache_fix.log
