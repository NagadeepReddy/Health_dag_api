SRC=/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max/cta_max/grecbase_integration_weights/att_pooling.rotary_emb.inv_freq.npy
DST=/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030/artifacts/v1.168-max/cta_max/sequence_weights/

if test -f "$SRC" && test -d "$DST"; then
  cp -nv "$SRC" "$DST"
  test -f "$DST/$(basename "$SRC")" && echo "CLEAN ROTARY WEIGHT: PASS"
else
  echo "STOP: Path missing"
fi
