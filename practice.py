
for d in \
  /application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max \
  /application1/cta_max_true_batch_dev_20261028/batch2_candidate \
  /application1/CTA_MAX_TRUE_BATCH2_DEV_20261029
do
  if [ -d "$d" ]; then
    find "$d" -type f -name 'fn_norm1_g.npy' -print 2>/dev/null
  fi
done
echo "WEIGHT LOCATION CHECK COMPLETE"
