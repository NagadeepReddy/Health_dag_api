SRC=/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030/artifacts/v1.168-max/cta_max/grecbase_integration_weights/att_pooling.rotary_emb_inv_freq.npy
DST=/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030/batch2/cta_max/sequence_weights/att_pooling.rotary_emb_inv_freq.npy

if test -f "$SRC" && test -d "$(dirname "$DST")"; then
  cp -n "$SRC" "$DST" &&
  echo "CLEAN ROTARY WEIGHT: PRESENT"
else
  echo "STOP: Source or destination directory missing"
fi
