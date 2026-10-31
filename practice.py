ROOT=/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030/artifacts/v1.168-max/cta_max

if [ -L "$ROOT/grecbase_integration_weights" ] &&
   [ -f "$ROOT/sequence_weights/seq_dense_weight.npy" ] &&
   [ ! -e "$ROOT/grecbase_integration_weights.link_backup" ] &&
   [ ! -e "$ROOT/.weights_stage" ] &&
   [ "$(df -Pk "$ROOT" | awk 'NR==2 {print $4}')" -gt 102400 ]; then

  mkdir "$ROOT/.weights_stage" &&
  cp -a "$ROOT/sequence_weights/." "$ROOT/.weights_stage/" &&

  test -f "$ROOT/.weights_stage/seq_dense_weight.npy" &&
  mv "$ROOT/grecbase_integration_weights" \
     "$ROOT/grecbase_integration_weights.link_backup" &&
  mv "$ROOT/.weights_stage" \
     "$ROOT/grecbase_integration_weights" &&

  echo "CLEAN REAL WEIGHT DIRECTORY: PASS"
else
  echo "STOP: Precheck failed; no changes attempted"
fi
