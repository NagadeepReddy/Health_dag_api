DIR=/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030/artifacts/v1.168-max/cta_max/grecbase_integration_weights

if test -f "$DIR/seq_dense_weight.npy"; then
  cp -n "$DIR/seq_dense_weight.npy" "$DIR/seq_dense.weight.npy"
  if cmp -s "$DIR/seq_dense_weight.npy" "$DIR/seq_dense.weight.npy"; then
    echo "CLEAN DENSE WEIGHT FILENAME: PASS"
  else
    echo "STOP: Filename fix verification failed"
  fi
else
  echo "STOP: Source weight missing"
fi
