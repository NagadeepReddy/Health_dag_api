ROOT=/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030
SRC="$ROOT/batch2/cta_max/sibling_context_weights"
DST="$ROOT/artifacts/v1.168-max/cta_max/sibling_context_weights"

if [ -f "$SRC/sibling_context_head.deep_embedding.0.weight.npy" ] &&
   [ ! -e "$DST" ] &&
   [ ! -L "$DST" ]; then

  cp -a "$SRC" "$DST" &&
  diff -qr "$SRC" "$DST" &&
  echo "CLEAN SIBLING WEIGHTS: PASS"
else
  echo "STOP: Source missing or destination already exists"
fi
