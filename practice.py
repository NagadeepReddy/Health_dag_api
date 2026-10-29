cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
find /application1/CTA_MAX_TRUE_BATCH2_DEV_20261029 \
     /application1/cta_max_true_batch_dev_20261028 \
     artifacts/v1.168-max \
     -type f \( -name 'run_batch2_contract.py' \
     -o -name '*batch2*runner*.py' \
     -o -name '*batch2*inference*.py' \) \
     -print 2>/dev/null | sort
