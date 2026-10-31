for dir in \
/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max \
/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029 \
/application1/cta_max_true_batch_dev_20261028
do
  echo "===== $dir ====="
  if [ -d "$dir" ]; then
    find "$dir" -type f \
      \( -name '*.py' -o -name '*.sh' -o -name '*.yaml' -o -name '*.yml' -o -name '*.toml' \) \
      ! -path '*/__pycache__/*' \
      ! -path '*/cta_native_batch2_release_candidate/*' \
      -printf '%p\n' | sort
  else
    echo "DIRECTORY NOT FOUND"
  fi
done
