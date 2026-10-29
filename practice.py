find /application1/CTA_MAX_TRUE_BATCH2_DEV_20261029 \
     /application1/cta_max_true_batch_dev_20261028 \
     -type f \( -name '*batch2*contract*.py' -o -name '*batch*contract*.py' \) \
     -print 2>/dev/null
