ARCH=/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029
SRC=/application1/cta_max_true_batch_dev_20261028/batch2_candidate/cta_max

test -f "$ARCH/batch2_source_review.tar.gz" &&
test -f "$SRC/run_batch2_contract.py" &&
tar -czf "$ARCH/batch2_complete_review.tar.gz" \
  -C "$ARCH" batch2_source_review.tar.gz \
  -C "$SRC" run_batch2_contract.py &&
echo "COMPLETE SOURCE PACKAGE: PASS" &&
ls -lh "$ARCH/batch2_complete_review.tar.gz"
