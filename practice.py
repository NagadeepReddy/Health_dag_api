ROOT=/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030
SRC="$ROOT/batch2/cta_max/main_context_weights"
DST="$ROOT/artifacts/v1.168-max/cta_max/main_context_weights"

if [ -f "$SRC/context_head.deep_embedding.0.weight.npy" ] &&
   [ ! -e "$DST" ] &&
   [ ! -L "$DST" ] &&
   [ "$(df -Pk "$(dirname "$DST")" | awk 'NR==2 {print $4}')" -gt "$(du -sk "$SRC" | awk '{print $1}')" ]; then
  cp -a "$SRC" "$DST" &&
  diff -qr "$SRC" "$DST" &&
  echo "CLEAN MAIN CONTEXT WEIGHTS: PASS"
else
  echo "STOP: Source, destination, or disk precheck failed"
fi
