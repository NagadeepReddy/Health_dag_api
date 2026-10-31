ROOT=/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030

SRC="$ROOT/batch2/cta_max/grecbase_integration_weights/seq_dense.weight.npy"
DST="$ROOT/artifacts/v1.168-max/cta_max/grecbase_integration_weights/seq_dense.weight.npy"

if test -f "$SRC" &&
   test -f "$DST" &&
   test ! -e "$DST.before_fix.bak" &&
   test ! -e "$DST.tmp"; then

  cp -p "$DST" "$DST.before_fix.bak" &&
  cp -p "$SRC" "$DST.tmp" &&
  cmp -s "$SRC" "$DST.tmp" &&
  mv -f "$DST.tmp" "$DST" &&
  cmp -s "$SRC" "$DST" &&
  echo "CLEAN CORRECT DENSE WEIGHT: PASS"

else
  echo "STOP: Precheck failed"
fi
