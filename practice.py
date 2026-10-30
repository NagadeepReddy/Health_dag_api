echo "=== SOURCE ARCHIVE ==="
ls -lh /application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/batch2_source_review.tar.gz

echo "=== LOCATE BATCH CONTRACT ==="
find \
/application1/cta_max_true_batch_dev_20261028/batch2_candidate \
/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029 \
-type f \( -name 'batch2_contract.py' -o -name 'run_batch2_contract.py' \) -print
